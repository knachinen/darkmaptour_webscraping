def clean_text(text: str) -> str:
    flag = True
    while flag:
        flag_space = True if '  ' in text else False
        flag_linefeed = True if '\n\n' in text else False
        if flag_space or flag_linefeed:
            if flag_space:
                text = text.replace('  ', ' ')
            if flag_linefeed:
                text = text.replace('\n\n', '\n')
        else:
            flag = False
    return text.strip()
