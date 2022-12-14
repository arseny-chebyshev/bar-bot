# Generated by Django 4.1.1 on 2022-09-16 13:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Dish',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('price', models.FloatField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='DishQuantity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField()),
                ('dish', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='db.dish')),
            ],
        ),
        migrations.CreateModel(
            name='Guest',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('debt', models.FloatField(default=0.0)),
            ],
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_ready', models.BooleanField(default=False)),
                ('total', models.FloatField(blank=True, null=True)),
                ('time', models.DateTimeField(auto_now_add=True)),
                ('dish', models.ManyToManyField(related_name='orders_with_dish', through='db.DishQuantity', to='db.dish')),
                ('guest', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='orders_from_guest', to='db.guest')),
            ],
        ),
        migrations.AddField(
            model_name='dishquantity',
            name='order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='db.order'),
        ),
    ]
