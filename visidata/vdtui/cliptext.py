import unicodedata
import sys
import functools

from visidata.vdtui import options

__all__ = ['clipstr', 'clipdraw']

disp_column_fill = ' '

### Curses helpers

def get_character_display_width(cc):
    '''Get the display width of a character.

    East Asian full-width characters are twice as wide as ASCII characters for
    terminal display.'''
    eaw = unicodedata.east_asian_width(cc)
    if eaw == 'A':  # ambiguous
        return options.disp_ambig_width
    elif eaw in 'WF': # wide/full
        return 2
    elif not unicodedata.combining(cc):
        return 1
    else:
        return 0

def get_string_display_width(ss):
    return sum( (get_character_display_width(cc) for cc in ss) )

@functools.lru_cache(maxsize=8192)
def clipstr(s, dispw):
    '''Return clipped string and width in terminal display characters.

    Note: width may differ from len(s) if East Asian chars are 'fullwidth'.'''
    w = 0
    ret = ''
    ambig_width = options.disp_ambig_width
    for c in s:
        if c != ' ' and unicodedata.category(c) in ('Cc', 'Zs', 'Zl'):  # control char, space, line sep
            c = options.disp_oddspace

        if c:
            c = c[0]  # multi-char disp_oddspace just uses the first char
            ret += c
            w += get_character_display_width(c)

        if w > dispw-len(options.disp_truncator)+1:
            ret = ret[:-2] + options.disp_truncator  # replace final char with ellipsis
            w += len(options.disp_truncator)
            break

    return ret, w


def clipdraw(scr, y, x, s, attr, w=None, rtl=False):
    'Draw string `s` at (y,x)-(y,x+w), clipping with ellipsis char.  if rtl, draw inside (x-w, x).  Returns width drawn (max of w).'
    if not scr:
        return 0
    _, windowWidth = scr.getmaxyx()
    dispw = 0
    try:
        if w is None:
            w = windowWidth-1
        w = min(w, (x-1) if rtl else (windowWidth-x-1))
        if w <= 0:  # no room anyway
            return 0

        # convert to string just before drawing
        clipped, dispw = clipstr(str(s), w)
        if rtl:
            # clearing whole area (w) has negative display effects; clearing just dispw area is useless
#            scr.addstr(y, x-dispw-1, disp_column_fill*dispw, attr)
            scr.addstr(y, x-dispw-1, clipped, attr)
        else:
            scr.addstr(y, x, disp_column_fill*w, attr)  # clear whole area before displaying
            scr.addstr(y, x, clipped, attr)
    except Exception as e:
        pass
#        raise type(e)('%s [clip_draw y=%s x=%s dispw=%s w=%s clippedlen=%s]' % (e, y, x, dispw, w, len(clipped))
#                ).with_traceback(sys.exc_info()[2])

    return dispw
