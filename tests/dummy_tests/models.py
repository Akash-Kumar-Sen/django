from django.db import models


class Business(models.Model):
    name = models.CharField(max_length=255)

    def approved_reviews(self):
        return self.review_set(manager="approved_reviews").all()


class ApprovedReviewsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=Review.APPROVED)


class Review(models.Model):
    NEW = 1
    APPROVED = 2
    STATUS_CHOICES = (
        (NEW, "New"),
        (APPROVED, "Approved"),
    )
    business = models.ForeignKey(Business, on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    status = models.IntegerField(choices=STATUS_CHOICES, default=NEW)

    objects = models.Manager()
    approved_reviews = ApprovedReviewsManager()
