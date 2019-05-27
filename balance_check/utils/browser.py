GET_IMG_BASE64 = (
    "const img = document.getElementById(arguments[0]);"
    "const canvas = document.createElement('canvas');"
    "const ctx = canvas.getContext('2d');"
    "ctx.drawImage(img, 0, 0);"
    "return canvas.toDataURL().replace(/data.*base64,/i, '');"
)


def get_image_b64_by_id(driver, img_id):
    return driver.execute_script(GET_IMG_BASE64, img_id)
