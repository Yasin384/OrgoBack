import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, UserProfile

# Настройка логирования
logger = logging.getLogger(__name__)  # Создаём экземпляр логгера

@receiver(post_save, sender=User)
def manage_user_profile(sender, instance, created, **kwargs):
    """
    Сигнал для создания или сохранения UserProfile при создании или обновлении User.
    """
    try:
        if created:
            UserProfile.objects.create(user=instance)
            logger.info(f"Создан профиль для пользователя: {instance.username}")
        else:
            instance.profile.save()  # Изменено с userprofile на profile
            logger.info(f"Обновлён профиль для пользователя: {instance.username}")
    except Exception as e:
        logger.error(f"Ошибка при управлении профилем пользователя {instance.username}: {e}")