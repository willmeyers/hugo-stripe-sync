import os
import argparse
import subprocess

def main():
    parser = argparse.ArgumentParser(description="Hugo Stripe Sync")
    parser.add_argument("--gh-token", required=True, help="A personal access token from GitHub")
    parser.add_argument("--git-repo-dir", required=False, default="/tmp/hugo_stripe_sync/")
    parser.add_argument("--git-remote", required=True, help="The git remote repository URL")
    parser.add_argument("--git-branch", required=False, default="main", help="The git branch to push to")
    parser.add_argument("--stripe-api-key", required=True, help="Stripe API key")
    parser.add_argument("--stripe-endpoint-secret", required=True, help="Stripe webhook enpoint secret key")
    args = parser.parse_args()

    os.environ["GH_TOKEN"] = args.gh_token
    os.environ["GIT_REPO_DIR"] = args.git_repo_dir
    os.environ["GIT_REMOTE"] = args.git_remote
    os.environ["GIT_BRANCH"] = args.git_branch
    os.environ["STRIPE_API_KEY"] = args.stripe_api_key
    os.environ["STRIPE_ENDPOINT_SECRET"] = args.stripe_endpoint_secret

    subprocess.run(["uvicorn", "src.service:service"])


if __name__ == "__main__":
    main()
