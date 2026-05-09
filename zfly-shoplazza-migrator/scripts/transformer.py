import json
from models import (
    ShoplazzaProductPayload,
    ShoplazzaProduct,
    ShoplazzaOption,
    ShoplazzaImage,
    ShoplazzaVariant,
)


def _to_price(val):
    if val is None:
        return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def _to_opt(val):
    if val is not None and val != "":
        return val
    return None


def parse_shopify_data(data: str) -> ShoplazzaProductPayload:
    raw = json.loads(data)
    p = raw.get("product", {})

    spz_p = ShoplazzaProduct(
        title=p.get("title", ""),
        handle=p.get("handle", ""),
        description=p.get("body_html", ""),
    )

    for opt in p.get("options", []):
        spz_p.options.append(ShoplazzaOption(name=opt["name"], values=opt["values"]))

    imgs = p.get("images", [])
    for img in imgs:
        spz_p.images.append(ShoplazzaImage(src=img["src"]))

    for i, v in enumerate(p.get("variants", [])):
        v_img = ShoplazzaImage(src=imgs[0]["src"]) if imgs else None
        for img in imgs:
            if img.get("id") == v.get("image_id"):
                v_img = ShoplazzaImage(src=img["src"])
                break

        spz_p.variants.append(
            ShoplazzaVariant(
                option1=_to_opt(v.get("option1")),
                option2=_to_opt(v.get("option2")),
                option3=_to_opt(v.get("option3")),
                price=_to_price(v.get("price", "0")),
                compare_at_price=(
                    _to_price(v.get("compare_at_price"))
                    if v.get("compare_at_price")
                    else None
                ),
                image=v_img,
                position=i + 1,
            )
        )
    return ShoplazzaProductPayload(product=spz_p)


def parse_shopline_data(data: str) -> ShoplazzaProductPayload:
    raw = json.loads(data)
    products = raw.get("products", [])
    if not products:
        raise ValueError("No products found in Shopline data")

    p = products[0]
    spz_p = ShoplazzaProduct(
        title=p.get("title", ""),
        handle=p.get("handle", ""),
        description=p.get("description", ""),
    )

    for opt in p.get("options", []):
        spz_p.options.append(ShoplazzaOption(name=opt["name"], values=opt["values"]))

    for img_url in p.get("images", []):
        spz_p.images.append(ShoplazzaImage(src=img_url))

    for i, v in enumerate(p.get("variants", [])):
        img_url = v.get("featured_image", "")
        if not img_url and v.get("featured_image_v2"):
            img_url = v["featured_image_v2"].get("url", "")

        spz_p.variants.append(
            ShoplazzaVariant(
                option1=_to_opt(v.get("option1")),
                option2=_to_opt(v.get("option2")),
                option3=_to_opt(v.get("option3")),
                price=float(v.get("price", 0)) / 100.0,
                compare_at_price=(
                    float(v.get("compare_at_price", 0)) / 100.0
                    if v.get("compare_at_price")
                    else None
                ),
                image=ShoplazzaImage(src=img_url) if img_url else None,
                position=i + 1,
            )
        )
    return ShoplazzaProductPayload(product=spz_p)


def detect_and_parse(data: str) -> ShoplazzaProductPayload:
    if '"shopify"' in data.lower() or '"body_html"' in data:
        return parse_shopify_data(data)
    elif '"products"' in data and '"featured_image"' in data:
        return parse_shopline_data(data)
    elif '"has_only_default_variant"' in data or '"inventory_quantity"' in data:
        raw = json.loads(data)
        p = raw.get("product", raw)
        spz_p = ShoplazzaProduct(
            id=str(p.get("id", "")),
            title=p.get("title", ""),
            handle=p.get("handle", ""),
            description=p.get("description", ""),
            has_only_default_variant=p.get("has_only_default_variant", False),
        )
        for opt in p.get("options", []):
            spz_p.options.append(
                ShoplazzaOption(name=opt["name"], values=opt["values"])
            )
        for img in p.get("images", []):
            spz_p.images.append(ShoplazzaImage(src=img.get("src", "")))
        for i, v in enumerate(p.get("variants", [])):
            v_img = None
            if v.get("image") and v["image"].get("src"):
                v_img = ShoplazzaImage(src=v["image"]["src"])
            spz_p.variants.append(
                ShoplazzaVariant(
                    option1=_to_opt(v.get("option1")),
                    option2=_to_opt(v.get("option2")),
                    option3=_to_opt(v.get("option3")),
                    price=_to_price(v.get("price", "0")),
                    compare_at_price=(
                        _to_price(v.get("compare_at_price"))
                        if v.get("compare_at_price")
                        else None
                    ),
                    image=v_img,
                    position=v.get("position", i + 1),
                )
            )
        return ShoplazzaProductPayload(product=spz_p)
    else:
        try:
            return parse_shopify_data(data)
        except:
            raise ValueError("Unsupported or unrecognizable product data format")
