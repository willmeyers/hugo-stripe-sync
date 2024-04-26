import io
import os
import json
import pathlib
 
from http import HTTPStatus
from typing import Annotated
 
import git
import git.repo
import stripe
from fastapi import Depends, FastAPI, Header, HTTPException, Request
 
 
stripe.api_key = os.environ["STRIPE_API_KEY"]


service = FastAPI()

 
async def get_body(request: Request) -> bytes:
    return await request.body()


async def get_git_remote() -> str:
    return os.environ["GIT_REMOTE"], os.environ["GIT_BRANCH"], os.environ["GIT_REPO_DIR"]


async def git_clone(git_remote_branch_dir: str = Depends(get_git_remote)):
    # TODO (willmeyers): add support for git_branch
    git_remote, git_branch, git_repo_dir = git_remote_branch_dir
    if not os.path.exists(git_repo_dir):
        os.makedirs(git_repo_dir)
    try:
        repo = git.Repo.clone_from(git_remote, git_repo_dir)
    except git.GitCommandError as e:
        if 'already exists and is not an empty directory' in str(e):
            repo = git.Repo(git_repo_dir)
            try:
                origin = repo.remote(name='origin')
                origin.pull()
            except Exception as e:
                print(f'Error: {str(e)}')
        else:
            raise e
    return repo

 
@service.post("/stripe_webhooks", status_code=HTTPStatus.NO_CONTENT)
def post_report(
    stripe_signature: Annotated[str, Header(alias="stripe-signature")],
    body: bytes = Depends(get_body),
    repo = Depends(git_clone)
) -> None:
    git_repo_dir = os.environ["GIT_REPO_DIR"]
    endpoint_secret = os.environ["STRIPE_ENDPOINT_SECRET"]
 
    try:
        # signature validation
        event = stripe.Webhook.construct_event(body, stripe_signature, endpoint_secret)
    except ValueError as e:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST) from e
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=HTTPStatus.UNPROCESSABLE_ENTITY) from e

    # TODO (willmeyers): add support for more events (product and price updates)
    if event["type"] == "charge.updated":
        ret = []
        r = stripe.Product.list()
        products = r["data"]
        for product in products:
            price_id = product.get("default_price")
            if price_id:
                default_price = stripe.Price.retrieve(price_id)
                product["default_price"] = default_price
            ret.append(product)
        
        print(pathlib.Path(git_repo_dir) / "data/products.json")
        with open(pathlib.Path(git_repo_dir) / "data/products.json", 'w+') as f:
            json.dump(ret, f)

        repo.index.add(['data/products.json'])
        repo.index.commit("Update products.json")
        repo.remotes.origin.push()

    return
