# coding=utf-8
import i18n
import config

i18n.load_path.append(
    '{}/translations'.format(config.ROOT_DIR)
)
i18n.set('file_format', 'json')
i18n.set('locale', 'vn')
i18n.set('filename_format', '{locale}.{format}')
i18n.set('skip_locale_root_data', True)


def _to_vn(messages):
    result = []
    for message in messages:
        result.append(i18n.t(message))
    return result


def vn(func):
    def func_wrapper(*args):
        message = func(*args)
        if isinstance(message, dict):
            message = _to_list(message)
            message = _to_vn(message)
            return '\n'.join(message)
        if isinstance(message, str):
            return i18n.t(message)
        return message

    return func_wrapper


def _to_list(data):
    if not isinstance(data, (dict, list)):
        return [str(data)]
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, list):
                return ['{} {}'.format(key, ', '.join(value))]
            return _to_list(value)
