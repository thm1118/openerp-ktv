# -*- coding: utf-8 -*-
import logging
from osv import fields, osv
import decimal_precision as dp
import ktv_helper
import fee_type

_logger = logging.getLogger(__name__)

class room_checkout_buyout(osv.osv):
    '''
    买断结账单,买断属于预售,应先付账,继承自ktv.room_checkout
    '''

    _name="ktv.room_checkout_buyout"

    _inherit = "ktv.room_checkout"

    _columns = {
            "buyout_config_id" : fields.many2one("ktv.buyout_config","buyout_config_id",required = True,select = True,help="买断名称"),
            "buyout_time_from" : fields.datetime("time_from",required = True,help="开房时间(此处指的是实际的开房时间)"),
            "buyout_time_to" : fields.datetime("time_to",required = True,help="关房时间"),
            "buyout_minutes" : fields.integer("buyout_minutes",help="买断时长"),
            "buyout_fee" : fields.float("buyout_fee",help="买断费用",digits_compute = dp.get_precision('Ktv Room Default Precision')),
            }
    _defaults = {
            #默认情况下,计费方式是买断
            "fee_type_id" : lambda obj,cr,uid,context: obj.pool.get('ktv.fee_type').get_fee_type_id(cr,uid,fee_type.FEE_TYPE_BUYOUT_FEE)
            }


    #buyout_config_id member_id fee_typeid 发生变化时
    def onchange_buyout_config_id(self,cr,uid,buyout_config_id,context):
        '''
        buyout_config_id 重新结算费用
        '''
        active_buyout_config = self.pool.get('ktv.buyout_config').get_active_buyout_fee(cr,uid,buyout_config_id)
        the_room = self.pool.get('ktv.room').browse(cr,uid,context["room_id"])

        hourly_fee = active_buyout_config['buyout_fee']

        ret ={
                'open_time': active_buyout_config['time_from'],
                'close_time': active_buyout_config['time_to'],
                'consume_minutes' : active_buyout_config['buyout_time'],
                #买断时,不收取其他费用,仅仅收取钟点费
                'hourly_fee' : hourly_fee,
                }

        #同时只能有一种打折方式可用
        #会员打折费用
        if 'member_id' in context and context['member_id']:
            the_member = self.pool.get('ktv.member').browse(cr,uid,context['member_id'])
            member_room_fee_discount_rate = the_member.member_class_id.room_fee_discount
            member_room_fee_discount_fee = hourly_fee*member_room_fee_discount_rate
            ret['member_room_fee_discount_rate'] = member_room_fee_discount_rate
            ret['member_room_fee_discount_fee'] = member_room_fee_discount_fee


        #打折卡打折
        if 'discount_card_id' in context and context['discount_card_id']:
            discount_card = self.pool.get('ktv.discount_card').browse(cr,uid,context['discount_card_id'])
            discount_card_room_fee_discount_rate = discount_card.room_fee_discount
            discount_card_room_fee_discount_fee = hourly_fee*discount_card_room_fee_discount_rate
            ret['discount_card_room_fee_discount_rate'] = discount_card_room_fee_discount_rate
            ret['discount_card_room_fee_discount_fee'] = discount_card_room_fee_discount_fee

        #员工打折
        #TODO
        #if 'discounter_id' in context and context['discounter_id']:
        return ret