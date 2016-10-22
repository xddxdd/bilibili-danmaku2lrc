# 全局设置
cfg = {
    # 获取弹幕池 ID 方式
    # - pagelist : 通过 http://www.bilibili.com/widget/getPageList API
    #   (视频标题可能无法正确显示)
    # - playpage : 通过视频播放网页
    #   (分P数量及分P标题可能无法正确显示)
    # - both : 两者兼用
    #   (多一个 HTTP 请求)
    'getDmidFrom' : 'both',
    # 字幕判断阈值
    # - 某个用户发送的底端/顶端弹幕达到这个数量以上才会被判断为弹幕
    'subtitleThreshold' : 10
}
# 主要代码开始
import requests

def stripStr(source, startFrom, endAt):
    posStart = source.find(startFrom)
    if(posStart == -1):
        return False
    posStart += len(startFrom)
    posStop = source.find(endAt, posStart)
    if(posStop == -1):
        return False
    return source[posStart : posStop]

def inputDigit(notification, minValue = 0, maxValue = 2147483647):
    n = input(notification)
    flag = True
    if(not n.isdigit()):
        flag = False
    else:
        if(int(n) < minValue or int(n) > maxValue):
            flag = False
    while(not flag):
        print('- ! 您的输入不符合要求')
        n = input(notification)
        flag = True
        if(not n.isdigit()):
            flag = False
        else:
            if(n < minValue or n > maxValue):
                flag = False
    return int(n)

def processDMLine(dmLine):
    dmMetaStart = dmLine.find('"') + 1
    dmMetaEnd = dmLine.find('"', dmMetaStart)
    dmMeta = dmLine[dmMetaStart : dmMetaEnd].split(',')
    dmData = {
        'pos' : float(dmMeta[0]),   # 时间轴坐标
        'sender' : dmMeta[6],       # sender id
        'dbid' : int(dmMeta[7]),    # database id
        'time' : int(dmMeta[4]),    # time danmaku sent
        'text' : dmLine[dmLine.find('">') + 2 : -4]
    }
    if(int(dmMeta[1]) >= 1 and int(dmMeta[1]) <= 3):
        dmData['type'] = 'standard'
    else:
        if(int(dmMeta[1]) == 4):
            dmData['type'] = 'bottom'
        else:
            if(int(dmMeta[1]) == 5):
                dmData['type'] = 'top'
            else:
                if(int(dmMeta[1]) == 6):
                    dmData['type'] = 'reverse'
                else:
                    if(int(dmMeta[1]) == 7):
                        dmData['type'] = 'advanced'
                    else:
                        if(int(dmMeta[1]) == 8):
                            dmData['type'] = 'code'
                        else:
                            dmData['type'] = dmMeta[1]
    if(int(dmMeta[2]) == 25):
        dmData['size'] = 'normal'
    else:
        if(int(dmMeta[2]) == 18):
            dmData['size'] = 'small'
        else:
            dmData['size'] = dmMeta[2]

    dmData['color'] = str(hex(int(dmMeta[3])))[2:]
    while(len(dmData['color']) < 6):
        dmData['color'] = '0' + dmData['color']

    if(int(dmMeta[5]) == 0):
        dmData['pool'] = 'standard'
    else:
        if(int(dmMeta[5]) == 1):
            dmData['pool'] = 'subtitle'
        else:
            if(int(dmMeta[5]) == 2):
                dmData['pool'] == 'advanced'
            else:
                dmData['pool'] == dmMeta[5]
    return dmData

def exportSubtitleDM(dmData):
    startPos = dmData.find('<d p=')
    if(startPos == -1):
        return False
    dmData = dmData[startPos : -6]
    dmArray = dmData.splitlines()
    response = []
    for dmLine in dmArray:
        dmMeta = processDMLine(dmLine)
        if(dmMeta['type'] == 'bottom' or dmMeta['type'] == 'top'):
            response += [dmMeta]
    return response

def second2LrcTag(pos):
    ms = int((pos - int(pos)) * 100)
    s = int(pos) % 60
    m = int(int(pos - s) / 60)
    response = '['
    if(m < 10):
        response += '0'
    response += str(m) + ':'
    if(s < 10):
        response += '0'
    response += str(s) + '.'
    if(ms < 10):
        response += '0'
    response += str(ms) + ']'
    return response

avID = inputDigit('? 输入视频 av 号: av', 1)
avPage = 0

if(cfg['getDmidFrom'] == 'pagelist' or cfg['getDmidFrom'] == 'both'):
    # pagelist 方式处理过程
    videoMetaRequest = requests.get('http://www.bilibili.com/widget/getPageList?aid=' + str(avID))
    if(videoMetaRequest.status_code != 200):
        # Fallback 到 playpage 方式
        print('X 获取 PageList API 失败, 转为直接获取播放页面')
        cfg['getDmidFrom'] = 'playpage'
    else:
        # 默认: 获取分P列表以获取弹幕池 ID
        videoMeta = videoMetaRequest.json()
        if(len(videoMeta) == 1):
            avPage = 1
        else:
            avPage = inputDigit('? 输入视频页码: (1 - %i) #' % len(videoMeta), 1, len(videoMeta))
if(cfg['getDmidFrom'] == 'playpage' or cfg['getDmidFrom'] == 'both'):
    # playpage 方式处理过程
    if(avPage == 0):
        avPage = inputDigit('? 输入视频页码: #', 1)
    if(avPage == 1):
        videoPage = requests.get('http://www.bilibili.com/video/av' + str(avID) + '/').text
    else:
        videoPage = requests.get('http://www.bilibili.com/video/av' + str(avID) + '/index_' + str(avPage) + '.html').text
        
if(cfg['getDmidFrom'] == 'playpage'):
    videoInfo = {
        'title' : stripStr(videoPage, '<title>', '</title>').split('_')[0],
        'id' : avID,
        'dmid' : int(stripStr(videoPage, 'cid=', '&'))
    }
if(cfg['getDmidFrom'] == 'pagelist'):
    videoInfo = {
        'title': videoMeta[avPage - 1]['pagename'],
        'id': avID,
        'dmid': int(videoMeta[avPage - 1]['cid'])
    }
if(cfg['getDmidFrom'] == 'both'):
    videoInfo = {
        'title': stripStr(videoPage, '<title>', '</title>').split('_')[0],
        'id': avID,
        'dmid': int(videoMeta[avPage - 1]['cid'])
    }
    if(videoMeta[avPage - 1]['pagename'] != ''):
        videoInfo['title'] += ' - ' + videoMeta[avPage - 1]['pagename']

print('i 视频标题: ' + videoInfo['title'])
print('i 视频av号: '+ str(videoInfo['id']))
print('i 弹幕池号: '+ str(videoInfo['dmid']))

if(videoInfo['dmid'] == 0):
    # 弹幕池 ID 获取失败
    print('X 视频弹幕池 ID 获取失败，原因可能是:')
    if(cfg['getDmidFrom'] == 'playpage' or cfg['getDmidFrom'] == 'both'):
        if(videoPage.find('http://static.hdslb.com/mstation/images/video/notfound')):
            print('  - 视频被删除')
            print('  - 视频只有会员能观看')
        else:
            print('  - Bilibili 改版, 原获取方式失效')
            print('  - 网络不稳定')
    else:
        print('  - 视频被删除')
        print('  - 视频只有会员能观看')
        print('  - Bilibili 改版, 原获取方式失效')
        print('  - 网络不稳定')
else:
    dmData = requests.get('http://comment.bilibili.com/%i.xml' % videoInfo['dmid']).text
    subtitleDmData = exportSubtitleDM(dmData)

    subtitleDmAuthors = {}
    for subtitleDmEntry in subtitleDmData:
        if(subtitleDmEntry['sender'] in subtitleDmAuthors):
            subtitleDmAuthors[subtitleDmEntry['sender']] += 1
        else:
            subtitleDmAuthors[subtitleDmEntry['sender']] = 1

    subtitleDmAuthorsAvailable = {}
    for subtitleDmAuthorSingle in subtitleDmAuthors.keys():
        if(subtitleDmAuthors[subtitleDmAuthorSingle] >= cfg['subtitleThreshold']):
            subtitleDmAuthorsAvailable[subtitleDmAuthorSingle] = subtitleDmAuthors[subtitleDmAuthorSingle]
    if(len(subtitleDmAuthorsAvailable) == 0):
        print('X 本视频中未发现野生字幕君')
    else:
        flag = False
        subtitleDmAuthorsKeys = list(subtitleDmAuthorsAvailable.keys())
        subtitleDmAuthorsKeys.sort()
        while(not flag):
            print('i 发现以下野生字幕君')
            i = 0
            for subtitleDmAuthorSingle in subtitleDmAuthorsKeys:
                i += 1
                print('- ' + str(i) + '. ' + subtitleDmAuthorSingle + ': ' + str(subtitleDmAuthorsAvailable[subtitleDmAuthorSingle]) + ' 条字幕')
            dmAuthorID = subtitleDmAuthorsKeys[inputDigit('? 您想要查看谁的字幕 #', 1, len(subtitleDmAuthorsAvailable)) - 1]
            subtitleDmSelected = []
            for subtitleDmEntry in subtitleDmData:
                if(subtitleDmEntry['sender'] == dmAuthorID):
                    subtitleDmSelected += [second2LrcTag(subtitleDmEntry['pos']) + subtitleDmEntry['text']]
            subtitleDmSelected.sort()
            print('i 野生字幕君 ' + dmAuthorID + ' 的字幕如下：')
            for subtitleDmEntry in subtitleDmSelected:
                print('- ' + subtitleDmEntry)
            if(input('? 您想要保存他的字幕吗 [y/N] ').upper() == 'Y'):
                flag = True
        saveFile = open('av' + str(avID) + '-P' + str(avPage) + '.lrc', 'w')
        for subtitleDmEntry in subtitleDmSelected:
            saveFile.write(subtitleDmEntry + '\r\n')
        saveFile.close()
        print('i 字幕文件已保存到 av' + str(avID) + '-P' + str(avPage) + '.lrc')