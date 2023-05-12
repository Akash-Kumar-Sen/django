from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.checks import Error
from django.db import models
from django.test import TestCase

from .models import Bar, Foo


class DatabaseLevelCascadeCheckTests(TestCase):
    def test_system_check_on_on_delete_db_combination(self):
        class MixedBar(models.Model):
            foo = models.ForeignKey(
                Foo,
                on_delete=models.CASCADE,
                on_delete_db=models.ON_DELETE_DB_CHOICES.CASCADE_DB,
            )

        mixed_bar_field = MixedBar._meta.get_field("foo")
        self.assertEqual(
            mixed_bar_field.check(),
            [
                Error(
                    "The on_delete must be set to on_delete=models.DB_CASCADE to work"
                    " with on_delete_db",
                    hint="Remove the on_delete_db or set on_delete=models.DB_CASCADE",
                    obj=mixed_bar_field,
                    id="fields.E322",
                )
            ],
        )

    def test_system_check_on_nested_db_with_non_db_cascading(self):
        class BadBar(models.Model):
            foo = models.ForeignKey(Foo, on_delete=models.CASCADE)

        class Baz(models.Model):
            """First level child"""

            bar = models.ForeignKey(
                Bar,
                on_delete=models.CASCADE,
                # on_delete_db=models.CASCADE
            )

        baz_field = Baz._meta.get_field("bar")
        self.assertEqual(
            baz_field.check(),
            [
                Error(
                    "Using normal cascading with DB cascading referenced model is "
                    "prohibited",
                    hint="Use database level cascading for foreignkeys",
                    obj=baz_field,
                    id="fields.E323",
                ),
            ],
        )

        bad_bar_field = BadBar._meta.get_field("foo")
        self.assertEqual(bad_bar_field.check(), [])

        bar_field = Bar._meta.get_field("foo")
        self.assertEqual(bar_field.check(), [])

    def test_null_condition_with_set_null_db(self):
        class SetNullDbNotNullModel(models.Model):
            foo = models.ForeignKey(
                Foo,
                on_delete=models.DB_CASCADE,
                on_delete_db=models.ON_DELETE_DB_CHOICES.SET_NULL_DB,
            )

            class Meta:
                managed = False

        field = SetNullDbNotNullModel._meta.get_field("foo")
        self.assertEqual(
            field.check(),
            [
                Error(
                    "Field specifies on_delete_db=SET_NULL_DB, but cannot be null.",
                    hint=(
                        "Set null=True argument on the field, or change the "
                        "on_delete_db rule."
                    ),
                    obj=field,
                    id="fields.E324",
                )
            ],
        )

    def test_check_on_inherited_models(self):
        class AnotherBar(Bar):
            another_foo = models.ForeignKey(
                Foo,
                on_delete=models.DB_CASCADE,
                on_delete_db=models.ON_DELETE_DB_CHOICES.CASCADE_DB,
            )

            class Meta:
                managed = False

        class MultipleInheritedBar(Foo, Bar):
            another_foo = models.ForeignKey(
                Foo,
                on_delete=models.DB_CASCADE,
                on_delete_db=models.ON_DELETE_DB_CHOICES.CASCADE_DB,
                related_name="another_foo",
            )

        field = AnotherBar._meta.get_field("another_foo")
        self.assertEqual(
            field.check(),
            [
                Error(
                    "Field specifies unsupported on_delete=DB_CASCADE, on "
                    "inherited model",
                    hint="Set a default value, or change the on_delete rule.",
                    obj=field,
                    id="fields.E325",
                )
            ],
        )

        multiple_inheritence_field = MultipleInheritedBar._meta.get_field("another_foo")
        self.assertEqual(
            multiple_inheritence_field.check(),
            [
                Error(
                    "Field specifies unsupported on_delete=DB_CASCADE, on "
                    "inherited model",
                    hint="Set a default value, or change the on_delete rule.",
                    obj=multiple_inheritence_field,
                    id="fields.E325",
                )
            ],
        )

    def test_check_on_generic_foreign_key(self):
        class SomeModel(models.Model):
            some_fk = models.ForeignKey(
                ContentType,
                on_delete=models.DB_CASCADE,
                on_delete_db=models.ON_DELETE_DB_CHOICES.CASCADE_DB,
                related_name="ctcmnt",
            )
            object_id = models.PositiveIntegerField()
            content_object = GenericForeignKey("some_fk", "object_id")

            class Meta:
                abstract = True

        class SomeAnotherModel(models.Model):
            another_fk = models.ForeignKey(
                ContentType, on_delete=models.CASCADE, related_name="anfk"
            )
            object_id = models.PositiveIntegerField()
            content_object = GenericForeignKey("another_fk", "object_id")

            class Meta:
                abstract = True

        comment_field = SomeModel._meta.get_field("some_fk")
        self.assertEqual(
            comment_field.check(),
            [
                Error(
                    "Field specifies unsupported on_delete=DB_CASCADE on model "
                    "declaring a GenericForeignKey.",
                    hint="Change the on_delete rule.",
                    obj=comment_field,
                    id="fields.E345",
                )
            ],
        )

        photo_field = SomeAnotherModel._meta.get_field("another_fk")
        self.assertEqual(
            photo_field.check(),
            [],
        )
