from catalog import models as m



def create_or_update_terminal_group(data):
    group_q = m.TerminalGroup.query.filter(
        m.TerminalGroup.code == data['code']
    )
    if group_q.first():
        group_q.update(data)
    else:
        group = m.TerminalGroup(**data)
        m.db.session.add(group)
    m.db.session.commit()
    return data, 'Create success'


def create_or_update_seller_terminal_group(data):
    mapping_q = m.SellerTerminalGroup.query.filter(
        m.SellerTerminalGroup.seller_id == data['seller_id'],
        m.SellerTerminalGroup.terminal_group_id == data['terminal_group_id']
    )
    if mapping_q.first():
        mapping_q.update(data)
    else:
        mapping = m.SellerTerminalGroup(**data)
        m.db.session.add(mapping)
    m.db.session.commit()
    return data, 'Create success'


def delete_seller_terminal_group(data):
    m.SellerTerminalGroup.query.filter(
        m.SellerTerminalGroup.seller_id == data['seller_id'],
        m.SellerTerminalGroup.terminal_group_id == data['terminal_group_id']
    ).delete()
    m.db.session.commit()
    return 'Delete success'


def delete_terminal_group_mapping(data):
    mapping_ids = [item['id'] for item in data]
    m.db.session.query(m.TerminalGroupTerminal).filter(
        m.TerminalGroupTerminal.id.in_(mapping_ids)
    ).delete(synchronize_session=False)
    m.db.session.commit()


def upsert_terminal_group_mapping(groups):
    for data in groups:
        mapping = m.TerminalGroupTerminal.query.get(data['id'])
        if mapping:
            mapping.termial_id = data['terminal']['id']
            mapping.terminal_group_id = data['group']['id']
        else:
            mapping = m.TerminalGroupTerminal(
                id=data['id'],
                terminal_code=data['terminal']['code'],
                terminal_group_code=data['group']['code']
            )
            m.db.session.add(mapping)
        m.db.session.query(m.TerminalGroup).filter(
            m.TerminalGroup.code == data['group']['code']
        ).update({'type': data['group']['type']})
    m.db.session.commit()


def mapping_terminal_group(data):
    op_type = data['op_type']
    if op_type == 'delete':
        delete_terminal_group_mapping(data['terminal_groups'])
    else:
        upsert_terminal_group_mapping(data['terminal_groups'])
    return {}, 'Update mapping success'
