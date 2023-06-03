from django.db.models import Prefetch
from django.test import TestCase

from .models import Business, Review

NEW = 1
APPROVED = 2
STATUS_CHOICES = (
    (NEW, "New"),
    (APPROVED, "Approved"),
)


class ApprovedReviewsTest(TestCase):
    def test_with_prefetch_Prefetch(self):
        business = Business()
        business.save()

        review = Review()
        review.business = business
        review.save()

        review = Review()
        review.business = business
        review.status = APPROVED
        review.save()

        prefetch_approved_reviews = Prefetch(
            "review_set", queryset=Review.approved_reviews.all()
        )
        businesses = Business.objects.prefetch_related(prefetch_approved_reviews).all()
        business = businesses[0]

        with self.assertNumQueries(0):
            # 0 queries while fetching the reviews when used prefetch
            approved_reviews = business.review_set.all()
            self.assertEqual(len(approved_reviews), 1)

    def test_without_prefetch(self):
        business = Business()
        business.save()

        review = Review()
        review.business = business
        review.save()

        review = Review()
        review.business = business
        review.status = APPROVED
        review.save()

        businesses = Business.objects.all()
        business = businesses[0]

        with self.assertNumQueries(1):
            # Making queries while fetching the reviews when not using prefetch
            approved_reviews = business.review_set(manager="approved_reviews").all()
            self.assertEqual(len(approved_reviews), 1)

    def test_with_prefetch(self):
        # This behaviour is not expected
        # But it is the cost of using prefetch
        business = Business()
        business.save()

        review = Review()
        review.business = business
        review.save()

        review = Review()
        review.business = business
        review.status = APPROVED
        review.save()
        businesses = Business.objects.prefetch_related("review_set").all()
        business = businesses[0]

        with self.assertNumQueries(0):
            # 0 queries while fetching the reviews when used prefetch
            approved_reviews = business.review_set(manager="approved_reviews").all()
            # Expected behaviour is 1, this is the bug
            self.assertEqual(len(approved_reviews), 2)
