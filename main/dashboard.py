# dashboard.py

from jet.dashboard.dashboard import Dashboard, AppIndexDashboard
from jet.dashboard.modules import DashboardModule, TableModule, LinkList
from django.utils.translation import ugettext_lazy as _
from .models import User, Leaderboard, Notification, Homework

# Custom Widget for User Overview
class UserOverviewModule(DashboardModule):
    title = _("User Overview")
    template = 'jet.dashboard.modules/user_overview.html'
    limit = 5  # Limit to 5 items

    def init_with_context(self, context):
        self.children = [
            {
                'total_users': User.objects.count(),
                'active_staff': User.objects.filter(is_staff=True).count(),
                'students': User.objects.filter(role='student').count(),
            }
        ]

# Custom Widget for Recent Notifications
class RecentNotificationsModule(TableModule):
    title = _("Recent Notifications")
    model = Notification
    template = 'jet.dashboard.modules/recent_notifications.html'
    limit = 5

    def init_with_context(self, context):
        self.children = Notification.objects.order_by('-created_at')[:self.limit]

# Custom Widget for Leaderboard
class LeaderboardModule(TableModule):
    title = _("Leaderboard")
    model = Leaderboard
    template = 'jet.dashboard.modules/leaderboard.html'
    limit = 10

    def init_with_context(self, context):
        self.children = Leaderboard.objects.order_by('-points')[:self.limit]

# Dashboard Configuration
class CustomIndexDashboard(Dashboard):
    columns = 3  # Define a 3-column layout

    def init_with_context(self, context):
        # Add User Overview
        self.children.append(UserOverviewModule())

        # Add Recent Notifications
        self.children.append(RecentNotificationsModule())

        # Add Leaderboard
        self.children.append(LeaderboardModule())

        # Add Links to Common Actions
        self.children.append(
            LinkList(
                title=_("Quick Actions"),
                children=[
                    {
                        'title': _('Add New User'),
                        'url': '/admin/main/user/add/',
                        'external': False,
                    },
                    {
                        'title': _('View All Classes'),
                        'url': '/admin/main/class/',
                        'external': False,
                    },
                ]
            )
        )

# Application Index Dashboard (Optional)
class CustomAppIndexDashboard(AppIndexDashboard):
    columns = 2  # Define a 2-column layout

    def init_with_context(self, context):
        # Add widgets for a specific app
        self.children.append(RecentNotificationsModule())
        self.children.append(LeaderboardModule())
