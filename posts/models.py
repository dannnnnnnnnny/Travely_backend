import re
from django.conf import settings
from django.db import models
from django.urls import reverse
from io import BytesIO
from PIL import Image
from django.core.files import File

# 타임스탬프
class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

# 게시물
class Post(TimestampedModel):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="my_post_set",on_delete=models.CASCADE)
    # tag_set = models.ManyToManyField("Tag", blank=True)
    like_user_set = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="like_post_set")
    is_quick = models.BooleanField() # 간편 true, 상세리뷰 false    
    start_date = models.DateField(auto_now=False, null=True)
    end_date = models.DateField(auto_now=False, null=True)
    rating = models.DecimalField(max_digits=2, decimal_places=1, null=True, blank=True)
    season = models.CharField(max_length=4, null=True, blank=True)

    def __str__(self):
        return (str(self.pk) + ' ' + str(self.author))

    def is_like_user(self, user):
        return self.like_user_set.filter(pk=user.pk).exists()

    class Meta:
        ordering = ['-id']

# 상세리뷰용 날짜
class PostDate(TimestampedModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="date")
    day = models.CharField(max_length=20, blank=True)
    caption = models.CharField(max_length=500, blank=True)
    tag_set = models.ManyToManyField("Tag", blank=True)
    #rating = models.DecimalField(max_digits=2, decimal_places=1, null=True, blank=True)
     
# 상세리뷰용 여행지
class DetailPostLocation(TimestampedModel):
    postdate = models.ForeignKey(PostDate, on_delete=models.CASCADE, related_name="detail_locations")
    location = models.CharField(max_length=100, blank=True)

def compress(image):
    im = Image.open(image)
    im_io = BytesIO() 
    im.save(im_io, 'JPEG', optimize=True, progressive=True, quality=70) 
    new_image = File(im_io, name=image.name)
    return new_image

# 상세리뷰용 이미지
class DetailPostImage(TimestampedModel):
    postdate = models.ForeignKey(PostDate, on_delete=models.CASCADE, related_name="detail_images")
    image = models.ImageField(upload_to="travely/post/%Y/%m/%d", null=True, blank=True, verbose_name='DetailImage')
    
    def save(self, *args, **kwargs):
                new_image = compress(self.image)
                self.image = new_image
                super().save(*args, **kwargs)

# 태그
class Tag(TimestampedModel):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

# 댓글
class Comment(TimestampedModel):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    like_user_set = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="like_comment_set")
    message = models.TextField()

    class Meta:
        ordering = ['created_at']
