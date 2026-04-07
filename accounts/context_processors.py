def family_context(request):
    """Inject family-level context into all templates."""
    context = {}
    if request.user.is_authenticated and request.user.family:
        from .models import User
        context['family'] = request.user.family
        context['family_kids'] = User.objects.filter(
            family=request.user.family, role=User.ROLE_CHILD
        ).order_by('-total_points')
        context['family_parents'] = User.objects.filter(
            family=request.user.family, role=User.ROLE_PARENT
        )
    return context
