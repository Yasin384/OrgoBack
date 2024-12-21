# main/signals.py

import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from django.core.cache import cache
from .models import User, UserProfile, UserAchievement

# Получаем логгер для текущего модуля
logger = logging.getLogger(__name__)

@receiver(post_save, sender=User)
def manage_user_profile(sender, instance, created, **kwargs):
    """
    Сигнал для создания или сохранения UserProfile при создании или обновлении User.
    """
    try:
        with transaction.atomic():
            if created:
                UserProfile.objects.create(user=instance)
                logger.info(f"Создан профиль для пользователя: {instance.username}")
            else:
                # Ensure that the UserProfile exists before saving
                user_profile, profile_created = UserProfile.objects.get_or_create(user=instance)
                if not profile_created:
                    user_profile.save()
                    logger.info(f"Обновлён профиль для пользователя: {instance.username}")
                else:
                    logger.info(f"Создан профиль для пользователя при обновлении: {instance.username}")
    except Exception as e:
        logger.error(f"Ошибка при управлении профилем пользователя {instance.username}: {e}")
        # Optionally, re-raise the exception if you want to propagate it
        # raise e

@receiver(post_save, sender=UserAchievement)
@receiver(post_delete, sender=UserAchievement)
def invalidate_leaderboard_cache(sender, **kwargs):
    """
    Invalidate the leaderboard cache when a UserAchievement is created, updated, or deleted.
    """
    try:
        cache.delete('leaderboard_data')
        logger.info("Leaderboard cache invalidated due to UserAchievement change.")
    except Exception as e:
        logger.error(f"Ошибка при инвалидации кэша лидеров: {e}")
