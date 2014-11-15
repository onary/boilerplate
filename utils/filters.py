def datetimeformat(value, format='%Y-%m-%d %H:%M'):
    return value.strftime(format)


def truncate_words(s, num=50, end_text='...'):
    s = unicode(s, 'utf8')
    length = int(num)
    if len(s) > length:
        s = s[:length]
        if not s[-1].endswith(end_text):
            s = s + end_text
    return s


def register_filters():
    return dict(
        truncate_words=truncate_words,
        datetimeformat=datetimeformat,
    )
