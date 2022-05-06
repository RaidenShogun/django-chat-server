from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Message(models.Model):
    #sender即是发送者,recipient即是接收者
    sender = models.ForeignKey(User,related_name='sent_messages',on_delete=models.SET_NULL,
                               blank=True,null=True,verbose_name='发送者')
    recipient = models.ForeignKey(User,related_name='receive_messages',on_delete=models.SET_NULL,
                                  blank=True,null=True,verbose_name='接收者')
    group = models.TextField(blank=False,null=False,verbose_name='组名')
    message = models.TextField(blank=True,null=True,verbose_name='内容')

    #unread是相对的,unread必定是recipient,所以这里的true或false是相对于recipient而言的
    unread = models.BooleanField(default=False,db_index=True,verbose_name='是否未读')
    create_time = models.DateTimeField(auto_now_add=True,verbose_name='创建时间')

class BlackList(models.Model):
    userid = models.ForeignKey(User,related_name='userid',on_delete=models.SET_NULL,
                               blank=True,null=True,verbose_name='用户id')
    blackuser = models.IntegerField(blank=True,null=True,verbose_name='黑名单用户')