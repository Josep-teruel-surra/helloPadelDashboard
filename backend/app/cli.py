"""Comandos de gestión. Uso: python -m app.cli --help"""

import asyncio

import typer
from fastapi import HTTPException
from pydantic import ValidationError

from app.core.database import SessionLocal, engine
from app.modules.users import service as users_service
from app.modules.users.models import UserRole
from app.modules.users.schemas import UserCreate

cli = typer.Typer(help="Comandos de gestión de helloPadelDashboard", no_args_is_help=True)


@cli.callback()
def main() -> None:
    pass


async def _create_admin(data: UserCreate) -> None:
    try:
        async with SessionLocal() as session:
            await users_service.create_user(session, data)
    finally:
        await engine.dispose()


@cli.command("create-admin")
def create_admin(
    email: str = typer.Option(..., prompt="Email"),
    full_name: str = typer.Option(..., "--name", prompt="Nombre completo"),
    password: str = typer.Option(
        ..., prompt="Contraseña", hide_input=True, confirmation_prompt=True
    ),
) -> None:
    """Crea una cuenta de administrador."""
    try:
        data = UserCreate(email=email, full_name=full_name, password=password, role=UserRole.ADMIN)
    except ValidationError as exc:
        for error in exc.errors():
            typer.secho(f"{error['loc'][0]}: {error['msg']}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc

    try:
        asyncio.run(_create_admin(data))
    except HTTPException as exc:
        typer.secho(str(exc.detail), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc

    typer.secho(f"Administrador {data.email} creado.", fg=typer.colors.GREEN)


if __name__ == "__main__":
    cli()
