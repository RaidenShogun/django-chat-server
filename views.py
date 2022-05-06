from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.generic import View
from .models import Message
from django.contrib.auth.models import User
import re
from django.db.models import Q    #Q对象能支持复杂查询

# Create your views here.

#以下代码中userone是当前用户,usertwo是想要私信的对象
class chatpage(View):
    def get(self,request):
        #通过session先判断用户是否登录,如果没登录或者session没有'is_login'这个key则都返回登录页面
        # try:
        #     is_login = request.session.get('is_login', False)
        #     if not is_login:
        #         return redirect('/login/')
        # except:
        #     return redirect('/login/')
        userone_id = request.session.get('userid')
        #返还最近15个与userone私聊的用户所形成的group
        recent_group = Message.objects.filter(Q(sender=userone_id) | Q(recipient=userone_id)).order_by(
                        '-create_time').values('group').distinct()[0:14]
        #将group拆开,获得最近私聊的其他用户id
        recent_userid = list()
        for onegroup in recent_group:
            users = re.findall("\d+",onegroup.group)   #提取group里面两个userID
            if int(users[0]) != userone_id:
                recent_userid.append(int(users[0]))  #如果第一个id是另一个用户的id,则添加进recent_user,否则添加第二个
            else:
                recent_userid.append(int(users[1]))
        #上面只是获取了id,这里我们要通过另一个用户的id去获取他在user数据库的所有数据如用户名、头像等,以字典形式返回
        recent_user_alldata = dict()
        for i in range(15):
            oneuserid = recent_userid[i]
            oneuser = User.objects.get(id=oneuserid)
            #获取和某一用户聊天的未读消息数
            oneuser.unread_count = Message.objects.filter(Q(sender=oneuserid)&Q(recipient=userone_id)
                                                        &Q(unread=True)).count()
            #获取最新一条和对方的聊天记录用于展示在最近私聊的用户列表中
            oneuser.recent_message = Message.objects.filter((Q(sender=userone_id)&Q(recipient=oneuserid)) |
                    (Q(sender=oneuserid)&Q(recipient=userone_id))).last()
            #字典的key以'user_1','user_2'...显示
            recent_user_alldata['user'+'_'+str(i)] = oneuser
        return render(request,'chat.html',recent_user_alldata)

#返回私聊信息是通过ajax实现的,将私聊信息包装成json返回,用户在chat页面通过点击一个另一用户进入聊天室并获取私聊记录
def message_ajax(request):
    all_json = dict()    #所有要返还的json数据
    userone_id = request.session.get('userid')  #通过session获取当前用户id,因为通过session获取故和下面userid不冲突
    usertwo_id = int(request.GET.get('userid'))  #通过ajax发过来的json数据包获取usertwo的id
    #为了传输快只要两用户的用户名和头像
    all_json['userone_alldata'] = User.objects.get(id=userone_id).values('username','user_photo')
    all_json['usertwo_alldata'] = User.objects.get(id=usertwo_id).values('username', 'user_photo')
    #获取双方聊天记录,这里是当用户在聊天页面点开与另一用户聊天界面时的返回值
    all_json['msgs'] = Message.objects.filter((Q(sender=userone_id)&Q(recipient=usertwo_id)) |
            (Q(sender=usertwo_id)&Q(recipient=userone_id))).order_by('-create_time').values('message')
    #将对方发送过来的未读消息全部更改成已读
    Message.objects.filter(Q(sender=usertwo_id)&Q(recipient=userone_id)).update(unread=False)
    #这个所谓的'all_msg'只是用户点击进入和一个人的聊天group的所有消息
    return JsonResponse(all_json)











