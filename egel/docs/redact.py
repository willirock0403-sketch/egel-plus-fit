from PIL import Image, ImageFilter

def redact(im, boxes, k, cell):
    for b in boxes:
        x0, y0, x1, y1 = [int(round(v*k)) for v in b]
        reg = im.crop((x0, y0, x1, y1))
        sm = reg.resize((max(1, (x1-x0)//cell), max(1, (y1-y0)//cell)), Image.BILINEAR)
        reg = sm.resize(reg.size, Image.NEAREST).filter(ImageFilter.GaussianBlur(cell*0.45))
        im.paste(reg, (x0, y0))
    return im

# ---- Recibo de tesorería (coordenadas a 935 px de ancho) ----
im = Image.open('reciboH-1.png').convert('RGB')
redact(im, [
    (228, 255, 524, 280),   # nombre
    (410, 281, 548, 307),   # matrícula
    (418, 431, 662, 458),   # fecha
], 2.0, 22)
im = im.crop((0, 0, im.width, int(600*2.0)))
im.save('../img/doc_recibo.jpg', quality=90)

# ---- Ficha de pago ----
im = Image.open('fichaH-1.png').convert('RGB')
redact(im, [
    (355, 38, 450, 60),     # número de ficha
    (580, 38, 695, 60),     # folio de facturación
    (450, 71, 518, 92),     # fecha de emisión
    (752, 72, 835, 91),     # fecha límite
    (288, 117, 660, 141),   # matrícula / folio + nombre
    (708, 206, 875, 228),   # CLABE
    (25, 368, 605, 405),    # código de barras
    (695, 378, 915, 405),   # referencia
    (40, 496, 915, 532),    # números de convenio / cuenta
    (335, 572, 650, 678),   # código de barras OXXO + número
], 2.0, 22)
im = im.crop((0, 0, im.width, int(690*2.0)))
im.save('../img/doc_ficha.jpg', quality=90)

# ---- Ficha con comprobante (ticket) en la esquina superior izquierda ----
K = 2624/765
im = Image.open('comprobante-1.png').convert('RGB')
redact(im, [
    (0, 0, 278, 60),        # encabezado de tienda (sucursal, domicilio)
    (0, 56, 278, 86),       # caja, fecha y hora
    (30, 100, 270, 142),    # pagada el día / ticket / folio de control
    (20, 140, 270, 160),    # referencia del ticket
    (60, 186, 250, 220),    # FOL / ID
    (283, 46, 355, 67),     # número de ficha
    (455, 46, 560, 67),     # folio de facturación
    (268, 76, 420, 94),     # fecha de emisión
    (590, 68, 668, 87),     # fecha límite
    (268, 108, 556, 130),   # matrícula + nombre
    (570, 180, 705, 202),   # CLABE
    (270, 312, 480, 348),   # código de barras
    (558, 316, 745, 340),   # referencia
    (268, 412, 765, 448),   # números de convenio / cuenta
    (0, 418, 278, 452),     # pie del ticket (hora / folio)
    (272, 495, 510, 572),   # código de barras OXXO + número
], K, 34)
im = im.crop((0, 0, im.width, int(585*K)))
im.save('../img/doc_comprobante.jpg', quality=88)
print('ok')
