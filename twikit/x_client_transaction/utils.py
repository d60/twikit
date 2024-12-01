import re
import bs4
import base64
from typing import Union


async def handle_x_migration(session, headers):
    home_page = None
    migration_redirection_regex = re.compile(
        r"""(http(?:s)?://(?:www\.)?(twitter|x){1}\.com(/x)?/migrate([/?])?tok=[a-zA-Z0-9%\-_]+)+""", re.VERBOSE)
    response = await session.request(method="GET", url="https://x.com", headers=headers)
    home_page = bs4.BeautifulSoup(response.content, 'lxml')
    migration_url = home_page.select_one("meta[http-equiv='refresh']")
    migration_redirection_url = re.search(migration_redirection_regex, str(
        migration_url)) or re.search(migration_redirection_regex, str(response.content))
    if migration_redirection_url:
        response = await session.request(method="GET", url=migration_redirection_url.group(0), headers=headers)
        home_page = bs4.BeautifulSoup(response.content, 'lxml')
    migration_form = home_page.select_one("form[name='f']") or home_page.select_one(f"form[action='https://x.com/x/migrate']")
    if migration_form:
        url = migration_form.attrs.get("action", "https://x.com/x/migrate") + "/?mx=2"
        method = migration_form.attrs.get("method", "POST")
        request_payload = {input_field.get("name"): input_field.get("value") for input_field in migration_form.select("input")}
        response = await session.request(method=method, url=url, data=request_payload, headers=headers)
        home_page = bs4.BeautifulSoup(response.content, 'lxml')
    return home_page


def float_to_hex(x):
    result = []
    quotient = int(x)
    fraction = x - quotient

    while quotient > 0:
        quotient = int(x / 16)
        remainder = int(x - (float(quotient) * 16))

        if remainder > 9:
            result.insert(0, chr(remainder + 55))
        else:
            result.insert(0, str(remainder))

        x = float(quotient)

    if fraction == 0:
        return ''.join(result)

    result.append('.')

    while fraction > 0:
        fraction *= 16
        integer = int(fraction)
        fraction -= float(integer)

        if integer > 9:
            result.append(chr(integer + 55))
        else:
            result.append(str(integer))

    return ''.join(result)


def is_odd(num: Union[int, float]):
    if num % 2:
        return -1.0
    return 0.0


def base64_encode(string):
    string = string.encode() if isinstance(string, str) else string
    return base64.b64encode(string).decode()


def base64_decode(input):
    try:
        data = base64.b64decode(input)
        return data.decode()
    except Exception:
        # return bytes(input, "utf-8")
        return list(bytes(input, "utf-8"))


if __name__ == "__main__":
    pass
