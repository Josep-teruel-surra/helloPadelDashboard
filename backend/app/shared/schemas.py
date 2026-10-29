from typing import Annotated, Any

from pydantic import AfterValidator, BeforeValidator, EmailStr, Field, StringConstraints

Email = Annotated[EmailStr, AfterValidator(str.lower)]
Password = Annotated[str, StringConstraints(min_length=8, max_length=128)]
FullName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]


def blank_to_none(value: Any) -> Any:
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value


def _lower(value: str | None) -> str | None:
    return value.lower() if value else value


# Código de país ISO 3166-1 alfa-2 ("es" → "ES").
CountryCode = Annotated[str, StringConstraints(pattern=r"^[A-Za-z]{2}$"), AfterValidator(str.upper)]

# Textos opcionales: "" o solo espacios se guardan como null. La restricción va en la rama str.
OptionalText120 = Annotated[
    Annotated[str, Field(max_length=120)] | None, BeforeValidator(blank_to_none)
]
OptionalText160 = Annotated[
    Annotated[str, Field(max_length=160)] | None, BeforeValidator(blank_to_none)
]
OptionalText200 = Annotated[
    Annotated[str, Field(max_length=200)] | None, BeforeValidator(blank_to_none)
]
OptionalShortText = Annotated[
    Annotated[str, Field(max_length=40)] | None, BeforeValidator(blank_to_none)
]
OptionalEmail = Annotated[EmailStr | None, BeforeValidator(blank_to_none), AfterValidator(_lower)]
OptionalCountryCode = Annotated[CountryCode | None, BeforeValidator(blank_to_none)]

Markdown = Annotated[str, Field(max_length=50_000)]
