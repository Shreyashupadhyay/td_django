# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Room',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=8, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_by', models.CharField(blank=True, max_length=100, null=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Player',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('join_order', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='players', to='game.room')),
            ],
            options={
                'ordering': ['join_order'],
            },
        ),
        migrations.CreateModel(
            name='GameState',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('round_number', models.IntegerField(default=1)),
                ('current_choice', models.CharField(blank=True, max_length=10, null=True)),
                ('is_waiting_for_question', models.BooleanField(default=False)),
                ('is_waiting_for_answer', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='game_states', to='game.room')),
                ('current_turn_player', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='current_turns', to='game.player')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('question_type', models.CharField(max_length=10)),
                ('source', models.CharField(choices=[('API', 'API'), ('ADMIN', 'Admin')], default='API', max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_answered', models.BooleanField(default=False)),
                ('game_state', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='game.gamestate')),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='game.room')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answer_text', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('player', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='game.player')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='game.question')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='player',
            constraint=models.UniqueConstraint(fields=('room', 'name'), name='game_player_room_name_unique'),
        ),
        migrations.AddConstraint(
            model_name='answer',
            constraint=models.UniqueConstraint(fields=('question', 'player'), name='game_answer_question_player_unique'),
        ),
    ]
