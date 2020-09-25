from django.contrib.auth import get_user_model
from django.db.models import Count
from rest_framework import serializers
from .models import Post, Comment, DetailPostImage, PostDate, Tag, DetailPostLocation
from django.forms.models import model_to_dict
from .sendPush import sendPush
import datetime, re
from accounts.models import MapData
from opendata.models import AreaCode

User = get_user_model()
api_url = "https://main.travely.kro.kr/media/"
# 작성자
class AuthorSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField('get_avatar')

    def get_avatar(self, obj):
        return api_url+str(obj.avatar)
        
    class Meta:
        model = User
        fields = ['name', 'nick_name', 'avatar'] # 이메일, 이름, 활동명, 프로필 사진

# 상세 리뷰 여행지
class DetailPostLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetailPostLocation
        fields = ['location']

# 상세 리뷰 이미지
class DetailPostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetailPostImage
        fields = ['image']

# 상세 리뷰 날짜
class PostDateSerializer(serializers.ModelSerializer):
    #detail_images = DetailPostImageSerializer(many=True, read_only=True)
    #detail_locations = DetailPostLocationSerializer(many=True, read_only=True)
    image_list = serializers.SerializerMethodField('image_list_set')
    location_list = serializers.SerializerMethodField('location_list_set')
    tag_list = serializers.SerializerMethodField("tag_list_set")
    
    def tag_list_set(self, postdate):
        data = []
        for tag in postdate.tag_set.all():
            data.append(tag.name)
        return data

    def image_list_set(self, postdate):
        data = []
        for d_image in postdate.detail_images.all():
            data.append(api_url+str(d_image.image))

        return data

    def location_list_set(self, postdate):
        data = []
        for d_location in postdate.detail_locations.all():
            data.append(d_location.location)
        return data

    class Meta:
        model = PostDate
        fields = [
            'day',
            'image_list',
            'location_list',
            'caption',
            'tag_list',
            #'rating',
        ]

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['name']


class PostSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    #date = PostDateSerializer(many=True, read_only=True)

    count = serializers.SerializerMethodField("image_count")
    image_list = serializers.SerializerMethodField("image_list_set")
    location_list = serializers.SerializerMethodField("location_list_set")
    caption_list = serializers.SerializerMethodField("caption_list_set")

    is_like = serializers.SerializerMethodField("is_like_field")
    like_count = serializers.SerializerMethodField("like_user_count")
    like_user_list = serializers.SerializerMethodField("like_user_list_set")
    comments_count = serializers.SerializerMethodField("comment_count")

    def image_count(self, post):
        data = []
        imageCount = post.date.values('id').annotate(Count('detail_images__image')).values('detail_images__image__count')
        for i_count in imageCount:
            data.append(i_count['detail_images__image__count'])
        
        return data

    def image_list_set(self, post):
        data = []
        imageList = post.date.values('detail_images__image')
        for i_list in imageList:
            data.append(api_url+str(i_list['detail_images__image']))
        return data
    
    def location_list_set(self, post):
        data = []
        locationList = post.date.values('detail_locations__location')
        for l_list in locationList:
            data.append(l_list['detail_locations__location'])
        return data
    
    def caption_list_set(self, post):
        data = []
        captionList = post.date.values('caption')
        for c_list in captionList:
            data.append(c_list['caption'])
        return data

    def comment_count(self, post):
        return post.comment_set.count()

    def like_user_list_set(self, post):
        data = []
        for l_user in post.like_user_set.values('nick_name'):
            data.append(l_user['nick_name'])
        return data

    def is_like_field(self, post):
        if "request" in self.context:
            user = self.context['request'].user
            return post.like_user_set.filter(pk=user.pk).exists()
        return False

    def like_user_count(self, post):
        return post.like_user_set.count()


    class Meta:
        model = Post
        fields = [
            'id',
            'is_quick',
            'author',
            'start_date',
            'end_date',
            #'date',
            # 'tag_list',
            
            'count',
            'image_list',
            'location_list',
            'caption_list',

            'rating',
            'is_like',
            'like_count',
            'like_user_list',
            'created_at',
            'comments_count',
            #'season',
        ]

    def create(self, validated_data):
        images_data = self.context['request'].FILES
        user = User.objects.get(pk=self.context['request'].user.pk)
        post = Post.objects.create(**validated_data)
        p = re.compile('[가-힣]{2}')
        is_quick = validated_data.get('is_quick') # 간편 / 상세 리뷰 확인
        user_tag = []
        
        if is_quick: # 간편 리뷰
            caption = self.context['request'].data['day1_caption']
            postdate = PostDate.objects.create(post=post,
                                               caption=caption, 
                                               day="day1") # day1

            user_tag = re.findall('(?:@([^\s]+))+', caption)
            user_tag = list(set(user_tag))

            tag_list = re.findall('(?:#([^\s]+))+', caption)
            for tag_data in tag_list:
                _tag, _ = Tag.objects.get_or_create(name=tag_data)
                postdate.tag_set.add(_tag)
            
            for location in self.context['request'].data.getlist('day1_location'):
                    DetailPostLocation.objects.create(postdate=postdate, location=location)
                    
                    map_name = p.findall(location)[0]
                    code = AreaCode.objects.get(name=map_name).code
                    md, created = MapData.objects.get_or_create(user=user, code=code, map_name=map_name)
                    # if created:
                    # else:
                    md.count += 1
                    md.save()

            for image_data in images_data.getlist('day1_image'):
                DetailPostImage.objects.create(postdate=postdate, image=image_data)

            user.exp = user.exp + 200

        else: # 상세 리뷰
            ## 날짜 계산
            start_d = self.context['request'].data['start_date']
            end_d = self.context['request'].data['end_date']
            
            season_date = int(start_d.split('-')[1])
            
            if season_date in [3,4,5]:
                season = "봄"
            elif season_date in [6,7,8]:
                season = "여름"
            elif season_date in [9,10,11]:
                season = "가을"
            else:
                season = "겨울"
            post.season = season

            start = datetime.datetime.strptime(start_d, "%Y-%m-%d").date()
            end = datetime.datetime.strptime(end_d, "%Y-%m-%d").date()

            for i in range((end - start).days+1):
                caption = self.context['request'].data['day'+str(i+1)+'_caption']
                postdate = PostDate.objects.create(post=post,
                                                 caption=caption, 
                                                 day="day"+str(i+1)) # day1,2,3

                date_user_tag = re.findall('(?:@([^\s]+))+', caption)
                date_user_tag = list(set(date_user_tag))
                user_tag += date_user_tag

                tag_list = re.findall('(?:#([^\s]+))+', caption)
                for tag_data in tag_list:
                    _tag, _ = Tag.objects.get_or_create(name=tag_data)
                    postdate.tag_set.add(_tag)

                for location in self.context['request'].data.getlist('day'+str(i+1)+'_location'):
                    DetailPostLocation.objects.create(postdate=postdate, location=location)

                    map_name = p.findall(location)[0]
                    code = AreaCode.objects.get(name=map_name).code
                    md, created = MapData.objects.get_or_create(user=user, map_name=map_name)
                    # if created:
                    # else:
                    md.count += 1
                    md.save()

                for image_data in images_data.getlist('day'+str(i+1)+'_image'):
                    DetailPostImage.objects.create(postdate=postdate, image=image_data)
            user.exp = user.exp + 300


        for user_name in list(set(user_tag)):
            try:
                f_token = get_user_model().objects.get(nick_name=user_name).fcm_token
                msg = self.context['request'].user.nick_name + "님이 게시물에 회원님을 언급했습니다."
                sendPush("게시물 알림", msg, str(f_token), "post_userTag")
                FCMAlarm.objects.create(user=f_token, div='post_tag', text=msg)
            except:
                pass
                #print("-fcm 토큰 부재-")

        user.save()
        return post


    def update(self, instance, validated_data):
        #images_data = self.context['request'].FILES
        rating = validated_data.get('rating')
        is_quick = validated_data.get('is_quick')
        user_tag = []

        post = Post.objects.get(pk=instance.id)
        if rating is None:
            pass
        else:
            post.rating = rating
    
        if is_quick:
            postdate = PostDate.objects.get(post=post, day="day1")
            try:
                caption = self.context['request'].data['day1_caption']
                postdate.caption = caption
                
                user_tag = re.findall('(?:@([^\s]+))+', caption)
                user_tag = list(set(user_tag))

                postdate.tag_set.clear()
                tag_list = re.findall('(?:#([^\s]+))+', caption)
                for tag_data in tag_list:
                    _tag, _ = Tag.objects.get_or_create(name=tag_data)
                    postdate.tag_set.add(_tag)
                
                postdate.save()
            except:
                pass

            # DetailPostLocation.objects.filter(postdate=postdate).delete()
            # for location in self.context['request'].data.getlist('day0_location'):
            #     DetailPostLocation.objects.create(postdate=postdate, location=location)
            
            # DetailPostImage.objects.filter(postdate=postdate).delete()
            # for image_data in images_data.getlist('day0_image'):
            #     DetailPostImage.objects.create(postdate=postdate, image=image_data)
        
        else:
            start_d = self.context['request'].data['start_date']
            end_d = self.context['request'].data['end_date']
            post.start_date = start_d
            post.end_date = end_d

            season_date = int(start_d.split('-')[1])
            
            if season_date in [3,4,5]:
                season = "봄"
            elif season_date in [6,7,8]:
                season = "여름"
            elif season_date in [9,10,11]:
                season = "가을"
            else:
                season = "겨울"
            post.season = season
            post.save()

            start = datetime.datetime.strptime(start_d, "%Y-%m-%d").date()
            end = datetime.datetime.strptime(end_d, "%Y-%m-%d").date()

            for i in range((end - start).days+1):
                caption = self.context['request'].data['day'+str(i+1)+'_caption']
                postdate = PostDate.objects.get(post=post, day='day'+str(i+1))
                postdate.caption = caption

                date_user_tag = re.findall('(?:@([^\s]+))+', caption)
                date_user_tag = list(set(date_user_tag))
                user_tag += date_user_tag

                postdate.tag_set.clear()
                tag_list = re.findall('(?:#([^\s]+))+', caption)
                for tag_data in tag_list:
                    _tag, _ = Tag.objects.get_or_create(name=tag_data)
                    postdate.tag_set.add(_tag)

                postdate.save()

                # DetailPostLocation.objects.filter(postdate=postdate).delete()
                # for location in self.context['request'].data.getlist('day'+str(i)+'_location'):
                #     DetailPostLocation.objects.create(postdate=postdate, location=location)

                # DetailPostImage.objects.filter(postdate=postdate).delete()
                # for image_data in images_data.getlist('day'+str(i)+'_image'):
                #     DetailPostImage.objects.create(postdate=postdate, image=image_data)

        for user_name in list(set(user_tag)):
            try:
                f_token = get_user_model().objects.get(nick_name=user_name).fcm_token
                msg = self.context['request'].user.nick_name + "님이 게시물에 회원님을 언급했습니다."
                sendPush("게시물 알림", msg, str(f_token), "post_userTag")
                FCMAlarm.objects.create(user=f_token, div='post_tag', text=msg)
            except:
                pass
                #print("-fcm 토큰 부재-")

        return post
        
class PostSearchSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    is_like = serializers.SerializerMethodField("is_like_field")
    like_count = serializers.SerializerMethodField("like_user_count")
    like_user_list = serializers.SerializerMethodField("like_user_list_set")
    day_list = serializers.SerializerMethodField("day_list_set")
    count = serializers.SerializerMethodField("image_count")
    image_list = serializers.SerializerMethodField("image_list_set")
    location_list = serializers.SerializerMethodField("location_list_set")
    caption_list = serializers.SerializerMethodField("caption_list_set")

    def image_count(self, post):
        keyword = self.context['kwargs']['keyword']
        search = self.context['kwargs']['search']
        data = []
        if search == 'location':
            search_list = post.date.filter(detail_locations__location__icontains=keyword)
        elif search == 'caption':
            search_list = post.date.filter(caption__icontains=keyword)
        elif search == 'tag':
            search_list = post.date.filter(tag_set__name__icontains=keyword)

        imageCount = search_list.distinct().values('day').annotate(Count('detail_images__image')).values('detail_images__image__count')
        for i_count in imageCount:
            data.append(i_count['detail_images__image__count'])
        return data

    def image_list_set(self, post):
        keyword = self.context['kwargs']['keyword']
        search = self.context['kwargs']['search']
        data = []
        if search == 'location':
            search_list = post.date.filter(detail_locations__location__icontains=keyword)
        elif search == 'caption':
            search_list = post.date.filter(caption__icontains=keyword)
        elif search == 'tag':
            search_list = post.date.filter(tag_set__name__icontains=keyword)

        imageList = search_list.values('detail_images__image')
        for i_data in imageList:
            data.append(api_url+i_data['detail_images__image'])
        return data
    
    def location_list_set(self, post):
        keyword = self.context['kwargs']['keyword']
        search = self.context['kwargs']['search']
        data = []
        if search == 'location':
            search_list = post.date.filter(detail_locations__location__icontains=keyword)
        elif search == 'caption':
            search_list = post.date.filter(caption__icontains=keyword)
        elif search == 'tag':
            search_list = post.date.filter(tag_set__name__icontains=keyword)

        locationList = search_list.values('detail_locations__location')
        for l_data in locationList:
            data.append(l_data['detail_locations__location'])
        return data
    
    def day_list_set(self, post):
        keyword = self.context['kwargs']['keyword']
        search = self.context['kwargs']['search']
        data = []
        if search == 'location':
            search_list = post.date.filter(detail_locations__location__icontains=keyword)
        elif search == 'caption':
            search_list = post.date.filter(caption__icontains=keyword)
        elif search == 'tag':
            search_list = post.date.filter(tag_set__name__icontains=keyword)

        dayList = search_list.values('day')
        for d_data in dayList:
            data.append(d_data['day'])
        return data

    def caption_list_set(self, post):
        keyword = self.context['kwargs']['keyword']
        search = self.context['kwargs']['search']
        data = []
        if search == 'location':
            search_list = post.date.filter(detail_locations__location__icontains=keyword)
        elif search == 'caption':
            search_list = post.date.filter(caption__icontains=keyword)
        elif search == 'tag':
            search_list = post.date.filter(tag_set__name__icontains=keyword)

        captionList = search_list.values('caption')
        for c_data in captionList:
            data.append(c_data['caption'])
        return data

    def like_user_list_set(self, post):
        data = []
        for l_user in post.like_user_set.values('nick_name'):
            data.append(l_user['nick_name'])
        return data

    def is_like_field(self, post):
        if "request" in self.context:
            user = self.context['request'].user
            return post.like_user_set.filter(pk=user.pk).exists()
        return False

    def like_user_count(self, post):
        return post.like_user_set.count()

    class Meta:
        model = Post
        fields = [
            'id',
            'is_quick',
            'author',
            'start_date',
            'end_date',    
            'count',
            'day_list',
            'image_list',
            'location_list',
            'caption_list',
            'rating',
            'is_like',
            'like_count',
            'like_user_list',
            'created_at',
            'season',
        ]

class TagSearchSerializer(serializers.Serializer):
    tag = serializers.SerializerMethodField("tag_name")
    count = serializers.SerializerMethodField("tag_count")

    def tag_name(self, obj):
        return obj['tag_set__name']

    def tag_count(self, obj):
        return obj['tag_set__name__count']


class CommentSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    is_like = serializers.SerializerMethodField("is_like_field")
    like_count = serializers.SerializerMethodField("like_user_count")
    like_user_list = serializers.SerializerMethodField("like_user_list_set")

    def like_user_list_set(self, comment):
        data = []
        for l_user in comment.like_user_set.values('nick_name'):
            data.append(l_user['nick_name'])
        return data

    def is_like_field(self, comment):
        if "request" in self.context:
            user = self.context['request'].user
            return comment.like_user_set.filter(pk=user.pk).exists()
        return False

    def like_user_count(self, comment):
        return comment.like_user_set.count()

    class Meta:
        model = Comment
        fields = ["id", "author", "message", "created_at", "is_like", "like_count", "like_user_list"]
