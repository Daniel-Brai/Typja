"""
FastAPI Example Application with Typja Template Type Checking

This example demonstrates how to set up a FastAPI application with Jinja2 templates
and configure Typja for template type checking.

To run this example:
  pip install fastapi uvicorn jinja2
  uvicorn app:app --reload

Then visit http://localhost:8000/profile/1
"""

from pathlib import Path

from fastapi import FastAPI  # type: ignore
from fastapi.requests import Request  # type: ignore
from fastapi.responses import HTMLResponse  # type: ignore
from fastapi.templating import Jinja2Templates  # type: ignore
from jinja2 import Environment, FileSystemLoader, select_autoescape
from models.user import User

TEMPLATES_DIR = Path(__file__).parent / "templates"

JINJA2_ENVIRONMENT = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    auto_reload=True,
    autoescape=select_autoescape(["html", "xml"]),
    extensions=["jinja2.ext.do"],
    trim_blocks=True,
    lstrip_blocks=True,
    optimized=True,
    cache_size=1000,
)

templates = Jinja2Templates(env=JINJA2_ENVIRONMENT)  # type: ignore

app = FastAPI(title="Typja FastAPI Example")


@app.get("/profile/{user_id}", response_class=HTMLResponse)
async def get_profile(user_id: int, request: Request) -> str:  # type: ignore
    """
    Render a user profile page with type-checked Jinja2 template.

    The template (profile.html) declares the `user` variable type using:
        {# typja:var user: User #}

    This allows Typja to verify that all variable accesses match the User type definition.
    """

    user = User(
        id=user_id,
        name=f"John Doe {user_id}",
        email=f"john{user_id}@example.com",
        is_active=True,
    )

    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={"user": user}
    )


@app.get("/users", response_class=HTMLResponse)
async def list_users(request: Request) -> str:  # type: ignore
    """
    Render a list of users with type-checked Jinja2 template.
    """

    users = [
        User(id=1, name="Alice Johnson", email="alice@example.com"),
        User(id=2, name="Bob Smith", email="bob@example.com"),
        User(id=3, name="Carol White", email="carol@example.com"),
    ]

    return templates.TemplateResponse(
        name="users_list.html",
        request=request,
        context={"users": users}
    )


if __name__ == "__main__":
    import uvicorn # type: ignore

    uvicorn.run(app, host="0.0.0.0", port=8000)
