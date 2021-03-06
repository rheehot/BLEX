import requests
import datetime
import random

from django.db import models
from django.db.models import Sum
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.template.defaultfilters import linebreaks
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape
from django.utils.timesince import timesince
from django.conf import settings

from PIL import Image

def randstr(length):
    rstr = '0123456789abcdefghijklnmopqrstuvwxyzABCDEFGHIJKLNMOPQRSTUVWXYZ'
    rstr_len = len(rstr) - 1
    result = ''
    for i in range(length):
        result += rstr[random.randint(0, rstr_len)]
    return result

def parsedown(text):
    data = {'md': text.encode('utf-8')}
    res = requests.post(settings.API_URL + '/api/safe-parsedown/get.php', data=data)
    return res.text

def avatar_path(instance, filename):
    dt = datetime.datetime.now()
    return 'images/avatar/u/' + instance.user.username + '/' + randstr(4) + '.' + filename.split('.')[-1]

def title_image_path(instance, filename):
    dt = datetime.datetime.now()
    return 'images/title/' + '/' + str(dt.year) + '/' + str(dt.month) + '/' + str(dt.day) + '/' + instance.author.username + '/' + str(dt.hour) + '_' + randstr(8) + '.' + filename.split('.')[-1]

def make_thumbnail(this, size, save_as=False, quality=100):
    if hasattr(this, 'avatar'):
        this.image = this.avatar
    image = Image.open(this.image)
    image.thumbnail((size, size), Image.ANTIALIAS)
    image.save('static/' + (str(this.image) if not save_as else this.get_thumbnail()), quality=quality)

class History(models.Model):
    user         = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    post         = models.ForeignKey('board.Post', on_delete = models.CASCADE)
    created_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.user.username

class Grade(models.Model):
    name = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.name

class Config(models.Model):
    user           = models.OneToOneField(User, on_delete=models.CASCADE)
    agree_email    = models.BooleanField(default=False)
    agree_history  = models.BooleanField(default=False)
    telegram_token = models.CharField(max_length=8, blank=True)
    telegram_id    = models.CharField(max_length=15, blank=True)
    password_qna   = models.TextField(blank=True)

    def __str__(self):
        return self.user.username

class Profile(models.Model):
    user       = models.OneToOneField(User, on_delete=models.CASCADE)
    subscriber = models.ManyToManyField(User, through='Follow', related_name='following', blank=True)
    grade      = models.ForeignKey('board.Grade', on_delete=models.CASCADE, blank=True, null=True)
    exp        = models.IntegerField(default=0)
    bio        = models.TextField(max_length=500, blank=True)
    avatar     = models.ImageField(blank=True,upload_to=avatar_path)
    github     = models.CharField(max_length=15, blank=True)
    twitter    = models.CharField(max_length=15, blank=True)
    youtube    = models.CharField(max_length=30, blank=True)
    facebook   = models.CharField(max_length=30, blank=True)
    instagram  = models.CharField(max_length=15, blank=True)
    homepage   = models.CharField(max_length=100, blank=True)
    about_md   = models.TextField()
    about_html = models.TextField()

    def thumbnail(self):
        if self.avatar:
            return self.avatar.url
        else:
            return settings.STATIC_URL + '/images/default-avatar.jpg'

    def __str__(self):
        return self.user.username
    
    def total_subscriber(self):
        return self.subscriber.count()

    def save(self, *args, **kwargs):
        will_make_thumbnail = False
        if not self.pk and self.avatar:
            will_make_thumbnail = True
        try:
            this = Profile.objects.get(id=self.id)
            if this.avatar != self.avatar:
                this.avatar.delete(save=False)
                will_make_thumbnail = True
        except:
            pass
        super(Profile, self).save(*args, **kwargs)
        if will_make_thumbnail:
            make_thumbnail(self, size=500)
    
    def get_absolute_url(self):
        return reverse('user_profile', args=[self.user])

class Follow(models.Model):
    class Meta:
        db_table = 'board_user_follow'
        auto_created = True
    
    following    = models.ForeignKey(Profile, on_delete=models.CASCADE)
    follower     = models.ForeignKey(User, on_delete=models.CASCADE)
    created_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.post.title

class Thread(models.Model):
    author            = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    title             = models.CharField(max_length=50)
    description       = models.TextField(blank=True)
    url               = models.SlugField(max_length=50, unique=True, allow_unicode=True)
    image             = models.ImageField(blank=True, upload_to=title_image_path)
    hide              = models.BooleanField(default=False)
    notice            = models.BooleanField(default=False)
    allow_write       = models.BooleanField(default=False)
    created_date      = models.DateTimeField(default=timezone.now)
    real_created_date = models.DateTimeField(default=timezone.now)
    tag               = models.CharField(max_length=50)
    bookmark          = models.ManyToManyField(User, related_name='bookmark_thread', blank=True)

    def __str__(self):
        return self.title

    def thumbnail(self):
        if self.image:
            return self.image.url
        else:
            return settings.STATIC_URL + '/images/default-post.png' if not self.image else self.image.url

    def total_bookmark(self):
        return self.bookmark.count()
    
    def tagging(self):
        return [tag for tag in self.tag.split(',') if tag]

    def today(self):
        count = 0
        try:
            today = timezone.make_aware(datetime.datetime.now())
            count = ThreadAnalytics.objects.get(date=today, thread=self).count
        except:
            pass
        return count
    
    def yesterday(self):
        count = 0
        try:
            yesterday = timezone.make_aware(datetime.datetime.now() - datetime.timedelta(days=1))
            count = ThreadAnalytics.objects.get(date=yesterday, thread=self).count
        except:
            pass
        return count

    def total(self):
        count = ThreadAnalytics.objects.filter(thread=self).aggregate(Sum('count'))
        if count['count__sum']:
            return count['count__sum']
        else:
            return 0
        
    def trendy(self):
        seven_days_ago = timezone.make_aware(datetime.datetime.now() - datetime.timedelta(days=7))
        today          = timezone.make_aware(datetime.datetime.now())
        count = ThreadAnalytics.objects.filter(date__range=[seven_days_ago, today], thread=self).aggregate(Sum('count'))
        if count['count__sum']:
            return count['count__sum']/10
        else:
            return 0

    def get_absolute_url(self):
        return reverse('thread_detail', args=[self.url])

    def get_thumbnail(self):
        return str(self.image) + '.minify.' + str(self.image).split('.')[-1]

    def to_dict_for_analytics(self):
        return {
            'pk': self.pk,
            'author': self.author.username,
            'title': self.title,
            'date': self.created_date,
            'today': self.today(),
            'yesterday': self.yesterday(),
            'total': self.total(),
            'hide': self.hide,
            'total_story': self.stories.count(),
            'total_bookmark': self.total_bookmark(),
            'tag': self.tag,
            'url': self.get_absolute_url(),
        }

    def save(self, *args, **kwargs):
        will_make_thumbnail = False
        if not self.pk and self.image:
            will_make_thumbnail = True
        try:
            this = Thread.objects.get(id=self.id)
            if this.image != self.image:
                this.image.delete(save=False)
                will_make_thumbnail = True
        except:
            pass
        super(Thread, self).save(*args, **kwargs)
        if will_make_thumbnail:
            make_thumbnail(self, size=750, save_as=True)

class ThreadAnalytics(models.Model):
    thread  = models.ForeignKey(Thread, on_delete=models.CASCADE)
    date    = models.DateField(default=timezone.now)
    count   = models.IntegerField(default=0)
    referer = models.TextField()
    iptable = models.TextField()

    def __str__(self):
        return self.thread.title

class Story(models.Model):
    class Meta:
        ordering = ['-created_date']
    
    thread       = models.ForeignKey('board.Thread', related_name='stories', on_delete = models.CASCADE)
    author       = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    title        = models.CharField(max_length=50)
    text_md      = models.TextField()
    text_html    = models.TextField()
    created_date = models.DateTimeField(default=timezone.now)
    updated_date = models.DateTimeField(default=timezone.now)
    agree        = models.ManyToManyField(User, related_name='agree_story', blank=True)
    disagree     = models.ManyToManyField(User, related_name='disagree_story', blank=True)

    def __str__(self):
        return self.title

    def total_disagree(self):
        return self.disagree.count()
    
    def total_agree(self):
        return self.agree.count()

    def to_dict(self):
        return {
            'pk': self.pk,
            'title': self.title,
            'author': self.author.username,
            'content': self.text_html,
            'agree': self.total_agree(),
            'disagree': self.total_disagree(),
            'thumbnail': self.author.profile.thumbnail(),
            'created_date': self.created_date.strftime("%Y-%m-%d %H:%M"),
            'updated_date': self.updated_date.strftime("%Y-%m-%d %H:%M"),
        }

class TempPosts(models.Model):
    author            = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    title             = models.CharField(max_length=50)
    token             = models.CharField(max_length=50)
    text_md           = models.TextField(blank=True)
    tag               = models.CharField(max_length=50)
    created_date      = models.DateTimeField(default=timezone.now)

    def to_dict(self):
        return {
            'title': self.title,
            'token': self.token,
            'text_md': self.text_md,
            'tag': self.tag,
            'created_date': timesince(self.created_date),
        }
    
    def __str__(self):
        return self.title

class Post(models.Model):
    author            = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    title             = models.CharField(max_length=50)
    url               = models.SlugField(max_length=50, unique=True, allow_unicode=True)
    image             = models.ImageField(blank=True, upload_to=title_image_path)
    text_md           = models.TextField(blank=True)
    text_html         = models.TextField()
    hide              = models.BooleanField(default=False)
    notice            = models.BooleanField(default=False)
    block_comment     = models.BooleanField(default=False)
    likes             = models.ManyToManyField(User, through='PostLikes', related_name='like_posts', blank=True)
    tag               = models.CharField(max_length=50)
    created_date      = models.DateTimeField(default=timezone.now)
    updated_date      = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return self.title

    def thumbnail(self):
        if self.image:
            return self.image.url
        else:
            return settings.STATIC_URL + '/images/default-post.png'

    def get_absolute_url(self):
        return reverse('post_detail', args=[self.author, self.url])

    def total_likes(self):
        return self.likes.count()
    
    def today(self):
        count = 0
        try:
            today = timezone.make_aware(datetime.datetime.now())
            count = PostAnalytics.objects.get(date=today, posts=self).count
        except:
            pass
        return count
    
    def yesterday(self):
        count = 0
        try:
            yesterday = timezone.make_aware(datetime.datetime.now() - datetime.timedelta(days=1))
            count = PostAnalytics.objects.get(date=yesterday, posts=self).count
        except:
            pass
        return count

    def total(self):
        count = PostAnalytics.objects.filter(posts=self).aggregate(Sum('count'))
        if count['count__sum']:
            return count['count__sum']
        else:
            return 0
        
    def trendy(self):
        seven_days_ago = timezone.make_aware(datetime.datetime.now() - datetime.timedelta(days=7))
        today          = timezone.make_aware(datetime.datetime.now())
        count = PostAnalytics.objects.filter(date__range=[seven_days_ago, today], posts=self).aggregate(Sum('count'))
        if count['count__sum']:
            return count['count__sum']/10
        else:
            return 0
    
    def tagging(self):
        return [tag for tag in self.tag.split(',') if tag]

    def get_thumbnail(self):
        return str(self.image) + '.minify.' + str(self.image).split('.')[-1]
    
    def to_dict_for_analytics(self):
        return {
            'pk': self.pk,
            'author': self.author.username,
            'title': self.title,
            'data': self.created_date,
            'today': self.today(),
            'yesterday': self.yesterday(),
            'total': self.total(),
            'hide': self.hide,
            'total_comment': self.comments.count(),
            'total_likes': self.total_likes(),
            'tag': self.tag,
            'url': self.get_absolute_url(),
        }

    def save(self, *args, **kwargs):
        will_make_thumbnail = False
        if not self.pk and self.image:
            will_make_thumbnail = True
        try:
            this = Post.objects.get(id=self.id)
            if this.image != self.image:
                this.image.delete(save=False)
                will_make_thumbnail = True
        except:
            pass
        super(Post, self).save(*args, **kwargs)
        if will_make_thumbnail:
            make_thumbnail(self, size=750, save_as=True)

class PostAnalytics(models.Model):
    posts   = models.ForeignKey(Post, on_delete=models.CASCADE)
    date    = models.DateField(default=timezone.now)
    count   = models.IntegerField(default=0)
    referer = models.TextField()
    iptable = models.TextField()

    def __str__(self):
        return self.posts.title

class PostLikes(models.Model):
    class Meta:
        db_table = 'board_post_likes'
        auto_created = True
    post         = models.ForeignKey(Post, on_delete=models.CASCADE)
    user         = models.ForeignKey(User, on_delete=models.CASCADE)
    created_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.post.title

class Comment(models.Model):
    author       = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    post         = models.ForeignKey('board.Post', related_name='comments', on_delete = models.CASCADE)
    text         = models.TextField(max_length=300)
    edit         = models.BooleanField(default=False)
    heart        = models.BooleanField(default=False)
    likes        = models.ManyToManyField(User, related_name='like_comments', blank=True)
    created_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.text
    
    def thumbnail(self):
        if self.image:
            return self.image.url
        else:
            return settings.STATIC_URL + '/images/default-post.png'
    
    def total_likes(self):
        return self.likes.count()
    
    def to_dict(self):
        return {
            'pk': self.pk,
            'author': self.author.username,
            'created_date': timesince(self.created_date),
            'content': linebreaks(escape(self.text)),
            'total_likes': self.total_likes(),
            'thumbnail': self.author.profile.thumbnail(),
            'edited': 'edited' if self.edit == True else '',
        }

class Notify(models.Model):
    user         = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    url          = models.CharField(max_length=255)
    is_read      = models.BooleanField(default=False)
    infomation   = models.TextField()
    created_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.infomation

    def to_dict(self):
        return {
            'pk': self.pk,
            'user': self.user.username,
            'infomation': self.infomation,
            'created_date': timesince(self.created_date)
        }

class Series(models.Model):
    owner        = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    name         = models.CharField(max_length=50, unique=True)
    description  = models.TextField(blank=True)
    url          = models.SlugField(max_length=50, unique=True, allow_unicode=True)
    posts        = models.ManyToManyField(Post, related_name='series', blank=True)
    created_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

    def thumbnail(self):
        if self.posts.first():
            return self.posts.first().thumbnail()
        else:
            return settings.STATIC_URL + '/images/default-post.png'
    
    def get_absolute_url(self):
        return reverse('series_list', args=[self.owner, self.url])