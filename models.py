from flask_admin_test import db
db.Model.metadata.reflect(db.engine)

from sqlalchemy.inspection import inspect


class Serializer(object):

    def serialize(self):
        return {c: getattr(self, c) for c in inspect(self).attrs.keys()}

    @staticmethod
    def serialize_list(l):
        return [m.serialize() for m in l]


class flow_meter(db.Model):
    __table__ = db.Model.metadata.tables['flow_meter']

    def __init__(self, flow_rate, timestamp):
        self.flow_rate = flow_rate
        self.timestamp = timestamp

    def __repr__(self):
        return 'ID:  ' + self.id


# class xero_logs(db.Model, Serializer):

#     __table__ = db.Model.metadata.tables['xero_logs']

#     def __init__(self, org_id):
#         self.org_id = org_id

#     def __repr__(self):
#         return 'xero_logs ' + self.org_id


# class qbo_logs(db.Model, Serializer):

#     __table__ = db.Model.metadata.tables['qbo_logs']

#     def __init__(self, org_id):
#         self.org_id = org_id

#     def __repr__(self):
#         return 'qbo_logs ' + self.org_id


# class sf_org_log(db.Model, Serializer):

#     __table__ = db.Model.metadata.tables['sf_org_log']

#     def __init__(self, org_id):
#         self.org_id = org_id

#     def __repr__(self):
#         return 'sf_org_log ' + self.id


# class subscriptions(db.Model, Serializer):

#     __table__ = db.Model.metadata.tables['subscriptions']

#     def __init__(self, sf_org_id, app, platform, account_state, billing_status, billing_method, alert_message, billing_frequency, plan_name, currency, multi_org, last_modified, invoice_tier, sub_domain, subscription_id, customer_id, current_price, current_period_ends_at):
#         self.sf_org_id = sf_org_id
#         self.app = app
#         self.platform = platform
#         self.account_state = account_state
#         self.billing_status = billing_status
#         self.billing_method = billing_method
#         self.alert_message = alert_message
#         self.billing_frequency = billing_frequency
#         self.plan_name = plan_name
#         self.currency = currency
#         self.multi_org = multi_org
#         self.last_modified = last_modified
#         self.invoice_tier = invoice_tier
#         self.sub_domain = sub_domain
#         self.subscription_id = subscription_id
#         self.customer_id = customer_id
#         self.current_price = current_price
#         self.current_period_ends_at = current_period_ends_at

#     def __repr__(self):
#         return 'subscriptions ' + self.sf_org_id


# class user_interaction_log(db.Model, Serializer):

#     __table__ = db.Model.metadata.tables['user_interaction_log']

#     def __init__(self, org_id):
#         self.org_id = org_id

#     def __repr__(self):
#         return 'user_interaction_log ' + self.org_id


# class xero_auth(db.Model, Serializer):

#     __table__ = db.Model.metadata.tables['xero_auth']

#     def __init__(self, org_id):
#         self.org_id = org_id

#     def __repr__(self):
#         return 'xero_auth ' + self.org_id


# class qbo_auth(db.Model, Serializer):

#     __table__ = db.Model.metadata.tables['qbo_auth']

#     def __init__(self, org_id):
#         self.org_id = org_id

#     def __repr__(self):
#         return 'qbo_auth ' + self.org_id


# class oauth_disconnection_log(db.Model, Serializer):

#     __table__ = db.Model.metadata.tables['oauth_disconnection_log']

#     # def __init__(self, org_id):
#     # 	self.org_id = org_id

#     def __repr__(self):
#         return 'oauth_disconnection_log ' + self.org_id


# class internal_logs(db.Model, Serializer):

#     __table__ = db.Model.metadata.tables['internal_logs']

#     def __repr__(self):
#         return 'internal_logs ' + self.org_id


# class day_hour_heatmap_test(db.Model, Serializer):

#     __table__ = db.Table('day_hour_heatmap', db.Model.metadata,
#                          db.Column('serial_number', db.BigInteger, primary_key=True),
#                          autoload=True, autoload_with=db.engine)

#     # def __init__(self, org_id):
#     # 	self.org_id = org_id

#     def __repr__(self):
#         return 'day_hour_heatmap ' + str(self.serial_number)


# class scratch_all_invoices(db.Model, Serializer):

#     __table__ = db.Model.metadata.tables['scratch_all_invoices']

#     def __repr__(self):
#         return 'scratch_all_invoices ' + self.sf_org_id


# class all_invoices(db.Model, Serializer):

#     __table__ = db.Model.metadata.tables['all_invoices']

#     def __init__(self, unique_id, sf_org_id, accounting_org_id, platform, total, total_tax, subtotal, status, invoice_date, accounting_updated_date, currency_code, due_date, fully_paid_date):
#         self.unique_id = unique_id,
#         self.sf_org_id = sf_org_id,
#         self.accounting_org_id = accounting_org_id,
#         self.platform = platform,
#         self.total = total,
#         self.total_tax = total_tax,
#         self.subtotal = subtotal,
#         self.status = status,
#         self.invoice_date = invoice_date,
#         self.accounting_updated_date = accounting_updated_date,
#         self.currency_code = currency_code,
#         self.due_date = due_date,
#         self.fully_paid_date = fully_paid_date

#     def __repr__(self):
#         return 'all_invoices ' + self.sf_org_id


# class subscription_status(db.Model, Serializer):
#     __table__ = db.Table('api_v2_subscription_response', db.Model.metadata,
#                          db.Column('org_id', db.String, db.ForeignKey('sf_org.org_id'), primary_key=True),
#                          autoload=True, autoload_with=db.engine)

#     # def __iter__(self):
#     # 	return iter(self._values)

#     # {'org_id':self.org_id,
#     # 		'postgresql_status':self.postgresql_status,
#     # 		'subscription_active':self.subscription_active,
#     # 		'plan_name':self.plan_name,
#     # 		'date_of_expiration':self.date_of_expiration,
#     # 		'app':self.app,
#     # 		'billing_token':self.billing_token,
#     # 		'multi_org':self.multi_org,
#     # 		'billing_status':self.billing_status,
#     # 		'invoice_tier':self.invoice_tier,
#     # 		'plan_code':self.plan_code,
#     # 		'active':self.active,
#     # 		'status':self.status,
#     # 		'sf_org_edition':self.sf_org_edition,
#     # 		'sf_org_type':self.sf_org_type,
#     # 		'installed_packages_number':self.installed_packages_number,
#     # 		'active_salesforce_users':self.active_salesforce_users,
#     # 		'active_platform_users':self.active_platform_users
#     # 		}

#     def __repr__(self):
#         return 'api_v2_subscription_response ' + self.org_id


# class active_subscriptions(db.Model, Serializer):
#     __table__ = db.Table('active_subscriptions', db.Model.metadata,
#                          db.Column('org_id', db.String, db.ForeignKey('sf_org.org_id'), primary_key=True),
#                          autoload=True, autoload_with=db.engine)

#     def __repr__(self):
#         return 'active_subscriptions ' + self.org_id


# class status_log(db.Model, Serializer):
#     __table__ = db.Table('status_log', db.Model.metadata,
#                          db.Column('log_id', db.String, db.ForeignKey('user_interaction_log.log_id'), primary_key=True),
#                          autoload=True, autoload_with=db.engine)

#     def __repr__(self):
#         return 'status_log ' + str(self.log_id)


# class auth_logs(db.Model, Serializer):
#     __table__ = db.Table('auth_logs', db.Model.metadata,
#                          db.Column('log_id', db.String, db.ForeignKey('user_interaction_log.log_id'), primary_key=True),
#                          autoload=True, autoload_with=db.engine)

#     def __repr__(self):
#         return 'auth_log ' + str(self.log_id)
