import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
#这里还需要一个黑名单的数据库,大概样式我会在models写一个
from django.db.models import Q
from .models import Message,BlackList

#所有通过session获取的id都是默认值故不需要类型转换
class ChatConsumer(AsyncWebsocketConsumer):
    guests = dict()   #这个是用来判断对方是否在房间内,用字典是因为要按照房间号区分
    async def connect(self):
        #使用session获取到本地用户id
        userone_id = self.scope['session']['userid']
        #user_two用url获取其id
        usertwo_id = self.scope['url_route']['kwargs'].get('userid')
        if self.check_user(userone_id,usertwo_id):
            # 拒绝黑名单用户用户连接
            await self.close()
        else:
            # 采用user_a的id加上下划线_加上user_b的id的方式来命名聊天组名。其中id值从小到大放置，例如：195752_748418
            if userone_id < int(usertwo_id):
                group_name = str(userone_id) + '_' + usertwo_id
            else:
                group_name = usertwo_id + '_' + str(userone_id)
            await self.accept()
            ChatConsumer.guests[group_name].add(userone_id)
            await self.channel_layer.group_add(group_name, self.channel_name)

    async def disconnect(self,disconnect_data):
        #离开聊天组，需要前端传过来一个断开的code,等最后确定是什么code我会把这个方法添加到receive()方法里
        #disconnect_data是在receive方法内已经得到group_name和userone_id后合并成的字典
        group_name = disconnect_data['group_name']
        userone_id = disconnect_data['userone_id']
        await self.channel_layer.group_discard(group_name, self.channel_name)
        ChatConsumer.guests[group_name].remove(userone_id)

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        message = data['message']
        group_name = data['group_name']  #因为所有的group都归这一个消费者管,所以需要前端发过来的group_name以区分不同的group
        userone_id = self.scope['session']['userid']
        disconnect_data = dict()
        disconnect_data['group_name'] = group_name
        disconnect_data['userone_id'] = userone_id
        usertwo_id = self.scope['url_route']['kwargs'].get('userid')
        userone_alldata = User.objects.get(id=userone_id)  # 从user数据库获取userone即发送者的用户名、头像
        userone_name = userone_alldata.username
        userone_photo = userone_alldata.user_photo
        # user_two用url获取其id
        #这里默认userone是sender,而usertwo是recipient
        if len(ChatConsumer.guests[group_name]) == 2:   #判断对方是否在聊天室内,若未在聊天室则这条消息对方未读
            await self.save_msg(userone_id, usertwo_id, group_name, message, False)
            # 发送消息
            await self.channel_layer.group_send(    #这个只发送双方的消息和用户名
                group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'username' : userone_name,
                    'user_photo' : userone_photo
                }
            )
        else:
            await self.save_msg(userone_id, usertwo_id, group_name, message, True)
            #若在线但不在聊天室内则还需把你发给对方的未读消息数也统计出来
            unread_count = Message.objects.filter(Q(sender=userone_id) & Q(recipient=usertwo_id)
                                                            & Q(unread=True)).count()
            await self.channel_layer.group_send(
                int(usertwo_id),   #向usertwo所在的那个独一无二的group把你的所有信息以及未读消息数发过去
                {
                    'type' : 'push_message',
                    'message': message,
                    'userid' : userone_id,
                    'username': userone_name,
                    'user_photo': userone_photo,
                    'unread_count' : unread_count
                }
            )

    async def chat_message(self,event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'username': event['username'],
        }),bytes_data=json.dumps({
            'user_photo': event['user_photo']
        })
        )

    async def push_message(self, event):    #这个push_message用来告诉那个不在房间的人你给他发消息了
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'userid' : event['userid'],
            'username': event['username'],
            'unread_count': event['unread_count']
        }),bytes_data=json.dumps({
            'user_photo': event['user_photo']
        })
        )

    async def save_msg(self,user1,user2,group,msg,unread):  #这里默认user1是sender,而user2是recipient
        Message.objects.create(sender=user1, recipient=int(user2), group=group, message=msg,unread=unread)

    #这是用来查询两用户是否在各自黑名单里，如果其中一方在另一方黑名单内则返回true,写两行只是单纯写一行会超
    #不使用async异步是因为必须要先执行这个方法再建立链接
    def check_user(self,user1,user2):
        #这里user1的id是通过session获取的,所以不需要类型转换
        if BlackList.objects.filter(userid=user1).exists(blackuser=int(user2)):
            return True
        if BlackList.objects.filter(userid=int(user2)).exists(blackuser=user1):
            return True
        return False

#这个consumer用来处理消息推送,用户一打开私信网页就向后端连入一个websocket,用于若不在房间还能收到别人发来的消息
class PushConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        #这里group_name就用用户id即可,每个用户有独立的group_name
        group_name = self.scope['session']['userid']
        await self.channel_layer.group_add(
            group_name,
            self.channel_name
        )
        await self.accept()

    # async def disconnect(self, code):
    #     #离开私聊网页，需要前端传过来一个断开的code
    #     PushConsumer.user_online.remove(group_name)
    #     await self.close()


