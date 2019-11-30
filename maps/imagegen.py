from PIL import Image, ImageDraw
import json
import os
import random

gids = set()


def determineMinMaxXY():
    xs = []
    ys = []
    minX = 10000
    maxX = 0
    minY = 10000
    maxY = 0
    for obj in jsondata['objects']:
        if obj.get('x') and obj.get('y'):
            xs.append(obj['x'])
            ys.append(obj['y'])
            if obj['x'] < minX:
                minX = obj['x']
            if obj['x'] > maxX:
                maxX = obj['x']
            if obj['y'] < minY:
                minY = obj['y']
            if obj['y'] > maxY:
                maxY = obj['y']
            gids.add(obj['gid'])

    # print(minX, maxX, maxX - minX)
    # print(minY, maxY, maxY - minY)
    # print(sorted(xs))
    # print(sorted(ys))
    return ((minX, maxX), (minY, maxY))


# determineMinMaxXY()
# -21000 57000 78000
# -12500 30500 43000


def generate_image_with_negative(locname):
    background = Image.new('RGBA', (78000 // 10, 43000 // 10), (0, 0, 0))

    for obj in jsondata['objects']:
        if obj.get('x') and obj.get('y'):
            tile = Image.new('RGBA', (500 // 10, 500 // 10), (255, 255, 255))
            draw = ImageDraw.Draw(tile)
            draw.text((1, 12), str(obj['gid']), (0, 0, 0))
            draw.text((1, 25), str(obj['objid']), (0, 0, 0))
            # tile.show()
            background.paste(tile, (obj['x'] // 10 + 21000 // 10, obj['y'] // 10 + 21000 // 10))

    background.save(f'export/negative/{locname}.png')
    print(locname)


table = str.maketrans(
    {'0': 'f', '1': 'e', '2': 'd', '3': 'c', '4': 'b', '5': 'a', '6': '9', '7': '8', '8': '7', '9': '6', 'a': '5', 'b': '4', 'c': '3', 'd': '2', 'e': '1', 'f': '0'}
)


def hextorgb(h):
    h = hex(h)[2:]
    while len(h) < 6:
        h = '0' + h
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def generate_image_no_negative(locname):
    # xSizes, ySizes = determineMinMaxXY()
    # width = abs(xSizes[0] + xSizes[1])
    # height = abs(ySizes[0] + ySizes[1])
    # print(locname, xSizes, ySizes, width, height)
    # return
    background = Image.new('RGBA', (36000 // 10, 17500 // 10), (0, 0, 0))

    for obj in jsondata['objects']:
        if obj.get('x') and obj.get('y') and obj['x'] > 0 and obj['y'] > 500 and obj['x'] < 36000 and obj['y'] < 18000:
            random.seed(obj['gid'])

            tilecolor = round((int(str(obj['gid'])[-3:]) / 491) * 0xffffff)
            textcolor = int('0x' + hex(tilecolor)[2:].translate(table), 16)

            tile = Image.new('RGBA', (500 // 10, 500 // 10), hextorgb(tilecolor))
            draw = ImageDraw.Draw(tile)
            draw.text((1, 12), str(obj['gid']), hextorgb(textcolor))
            draw.text((1, 25), str(obj['objid']), hextorgb(textcolor))
            # tile.show()
            background.paste(tile, (obj['x'] // 10, (obj['y'] - 500) // 10))

    background.save(f'export/{locname}.png')
    print(locname)


for i in os.listdir('../locations'):
    if i.endswith('.loc.json'):
        file = f'../locations/' + i
        with open(file) as f:
            jsondata = json.load(f)

        generate_image_no_negative(i.replace('.loc.json', ''))
        # determineMinMaxXY()
