# -*- coding: UTF-8 -*-

import os
import time
import hmac
import base64
import string
import random
import secrets
import datetime
import itertools
import functools
import threading
import unicodedata


CHARACTERS = string.digits + string.ascii_letters
SECRET_PHRASE = ''.join(secrets.choice(CHARACTERS) for _ in range(9)).encode()
BASE64_ALTCHARS = ''.join(secrets.choice(CHARACTERS) for _ in range(2)).encode()


def run_async(func):
    @functools.wraps(func)
    def decorator(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.start()
        return thread
    return decorator


def get_token():
    '''Generate a token ensuring that it does not repeat.'''
    stamp = int(time.time() * 1e8).to_bytes(9, byteorder='big')
    digest = hmac.digest(SECRET_PHRASE, stamp, 'sha256')
    token = base64.b64encode(digest, altchars=BASE64_ALTCHARS).decode()
    return token.rstrip('=')


def change_seed(num=0):
    '''Random seed change, improves randomness.'''
    seed = time.time() + int.from_bytes(os.urandom(4), byteorder='big')
    random.seed(seed + float(num or 0))


def remove_diacritics(text):
    '''Remove the Mark and Nonspacing characters from the text.'''
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in nfkd if unicodedata.category(c) != 'Mn')


def time_to_text(delta):
    if isinstance(delta, (int, float)):
        delta = datetime.timedelta(seconds=delta)
    elif not isinstance(delta, datetime.timedelta):
        raise NotImplementedError(f'for {delta!r} {type(time)}')

    parts = str(delta).split()
    if len(parts) == 3:
        days = parts[0]
        hms = parts[2]
    else:
        days = 0
        hms = parts[0]
    hour, minute, second = hms.split(':')
    phrase = []
    items = (
        (int(days), 'día', 'días'),
        (int(hour), 'hora', 'horas'),
        (int(minute), 'minuto', 'minutos'),
        (int(second), 'segundo', 'segundos')
    )
    for number, singular, plural in items:
        if number == 1:
            phrase.append(f'{number} {singular}')
        elif number != 0:
            phrase.append(f'{number} {plural}')
    if len(phrase) == 1:
        return phrase[-1]

    return ', '.join(phrase[:-1]) + ' y ' + phrase[-1]


def take(num, iterable):
    '''Return first *num* items of the iterable as a list.

        >>> take(3, range(10))
        [0, 1, 2]
        >>> take(5, range(3))
        [0, 1, 2]

    Effectively a short replacement for ``next`` based iterator consumption
    when you want more than one item, but less than the whole iterator.

    github.com/erikrose/more-itertools
    '''
    return list(itertools.islice(iterable, num))


def chunked(iterable, num):
    '''Break *iterable* into lists of length *num*:

        >>> list(chunked([1, 2, 3, 4, 5, 6], 3))
        [[1, 2, 3], [4, 5, 6]]

    If the length of *iterable* is not evenly divisible by *num*, the last
    returned list will be shorter:

        >>> list(chunked([1, 2, 3, 4, 5, 6, 7, 8], 3))
        [[1, 2, 3], [4, 5, 6], [7, 8]]

    :func:`chunked` is useful for splitting up a computation on a large number
    of keys into batches, to be pickled and sent off to worker processes. One
    example is operations on rows in MySQL, which does not implement
    server-side cursors properly and would otherwise load the entire dataset
    into RAM on the client.

    github.com/erikrose/more-itertools
    '''
    return iter(functools.partial(take, num, iter(iterable)), [])
