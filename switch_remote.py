#!/usr/bin/env python3
"""
切换 Git 远程仓库脚本
自动更新 remote origin 并推送到新仓库
"""
import subprocess
import sys
import requests
import os


def get_github_token():
    """从环境变量或配置文件获取 GitHub Token"""
    # 从环境变量获取
    token = os.getenv("GITHUB_TOKEN")
    if token:
        return token

    # 从 auto-chaoxin config.json 获取
    try:
        import json
        from pathlib import Path
        config_path = Path("/Users/baofuzhang/ppp/auto-chaoxin/config.json")
        if config_path.exists():
            with open(config_path, "r") as f:
                config = json.load(f)
                return config.get("github", {}).get("token")
    except:
        pass

    return None


def get_github_username(token):
    """获取 GitHub 用户名"""
    try:
        response = requests.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github+json",
            }
        )
        if response.status_code == 200:
            return response.json()["login"]
    except:
        pass
    return None


def list_github_repos(token, username):
    """列出用户的所有仓库"""
    try:
        response = requests.get(
            f"https://api.github.com/users/{username}/repos",
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github+json",
            },
            params={
                "sort": "updated",
                "per_page": 100
            }
        )

        if response.status_code == 200:
            repos = response.json()
            return [(repo["name"], repo["html_url"]) for repo in repos]
    except Exception as e:
        print(f"⚠️ 获取仓库列表失败: {e}")

    return []


def get_current_remote():
    """获取当前的远程仓库地址"""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def switch_remote(new_repo_url):
    """切换到新的远程仓库"""
    current = get_current_remote()

    print("=" * 60)
    print("🔄 切换 Git 远程仓库")
    print("=" * 60)

    if current:
        print(f"\n📍 当前远程仓库: {current}")
    else:
        print("\n⚠️  未找到远程仓库")

    print(f"🎯 新远程仓库: {new_repo_url}")

    # 确认操作
    confirm = input("\n确认切换? (y/n): ")
    if confirm.lower() != 'y':
        print("❌ 操作已取消")
        return False

    try:
        # 移除旧的 origin
        if current:
            subprocess.run(["git", "remote", "remove", "origin"], check=True)
            print("✅ 已移除旧的远程仓库")

        # 添加新的 origin
        subprocess.run(["git", "remote", "add", "origin", new_repo_url], check=True)
        print("✅ 已添加新的远程仓库")

        # 推送到新仓库
        print("\n📤 推送代码到新仓库...")
        subprocess.run(["git", "push", "-u", "origin", "main", "--force"], check=True)
        print("✅ 代码推送成功")

        print("\n" + "=" * 60)
        print("✅ 远程仓库切换完成！")
        print("=" * 60)
        return True

    except subprocess.CalledProcessError as e:
        print(f"\n❌ 操作失败: {e}")
        return False


def main():
    print("=" * 60)
    print("📦 GitHub 仓库切换工具")
    print("=" * 60)

    # 获取 GitHub Token
    token = get_github_token()
    if not token:
        print("\n❌ 未找到 GitHub Token")
        print("请设置环境变量: export GITHUB_TOKEN=your_token")
        print("或确保 auto-chaoxin/config.json 存在")
        sys.exit(1)

    # 获取用户名
    username = get_github_username(token)
    if not username:
        print("\n❌ 无法获取 GitHub 用户信息")
        sys.exit(1)

    print(f"\n👤 GitHub 用户: {username}")

    # 获取当前远程仓库
    current = get_current_remote()
    if current:
        print(f"📍 当前仓库: {current}")

    # 获取仓库列表
    print("\n🔍 正在获取仓库列表...")
    repos = list_github_repos(token, username)

    if not repos:
        print("❌ 未找到仓库")
        sys.exit(1)

    # 显示仓库列表
    print("\n" + "=" * 60)
    print("📚 可用仓库列表 (按更新时间排序)")
    print("=" * 60)

    for i, (repo_name, repo_url) in enumerate(repos, 1):
        # 标记当前仓库
        marker = " ⭐ (当前)" if current and repo_name in current else ""
        print(f"{i:2d}. {repo_name}{marker}")

    # 选择仓库
    print("\n" + "-" * 60)
    try:
        choice = input("输入仓库编号 (或 'q' 退出): ").strip()

        if choice.lower() == 'q':
            print("❌ 已取消")
            sys.exit(0)

        choice_num = int(choice)
        if choice_num < 1 or choice_num > len(repos):
            print("❌ 无效的选择")
            sys.exit(1)

        selected_repo = repos[choice_num - 1]
        repo_name, repo_url = selected_repo

        # 构造带 Token 的 URL
        new_repo_url = repo_url.replace("https://", f"https://{token}@")

        print(f"\n🎯 已选择: {repo_name}")
        switch_remote(new_repo_url)

    except ValueError:
        print("❌ 请输入有效的数字")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n❌ 已取消")
        sys.exit(0)


if __name__ == "__main__":
    main()
