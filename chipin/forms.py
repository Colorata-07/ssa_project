from django import forms
from .models import Group

class GroupCreationForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        group = super().save(commit=False)
        group.admin = self.user  # Assign the logged-in user as the admin
        if commit:
            group.save()
            group.members.add(self.user)  # Add the admin to the members list
        return group
    
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter your comment...'})
        }

    # Clean the content to sanitise input
    def clean_content(self):
        content = self.cleaned_data.get('content')
        if "<script>" in content.lower():  # Prevent XSS by checking for script tags
            raise forms.ValidationError("Invalid content.")
        return content
    
@login_required
def group_detail(request, group_id, edit_comment_id=None):
    group = get_object_or_404(Group, id=group_id)
    comments = group.comments.all().order_by('-created_at')  # Fetch all comments for the group
    if edit_comment_id: # Fetch the comment to edit, if edit_comment_id is provided
        comment_to_edit = get_object_or_404(Comment, id=edit_comment_id)
        if comment_to_edit.user != request.user:
            return redirect('chipin:group_detail', group_id=group.id)
    else:
        comment_to_edit = None
    if request.method == 'POST':
        if comment_to_edit: # Editing an existing comment
            form = CommentForm(request.POST, instance=comment_to_edit)
        else: # Adding a new comment
            form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.group = group
            comment.save()
            return redirect('chipin:group_detail', group_id=group.id)
    else:
        form = CommentForm(instance=comment_to_edit) if comment_to_edit else CommentForm()
    return render(request, 'chipin/group_detail.html', {
        'group': group,
        'comments': comments,
        'form': form,
        'comment_to_edit': comment_to_edit,
    })

@login_required
def home(request):
    user = request.user
    pending_invitations = user.pending_invitations.all() # Get pending group invitations for the current user
    user_groups = user.group_memberships.all()  # Get groups the user is a member of
    user_join_requests = GroupJoinRequest.objects.filter(user=user)  # Get join requests sent by the user
    available_groups = Group.objects.exclude(members=user).exclude(join_requests__user=user) # Get groups the user is not a member of and the user has not requested to join
    context = {
        'pending_invitations': pending_invitations,
        'user_groups': user_groups,
        'user_join_requests': user_join_requests,
        'available_groups': available_groups
    }
    return render(request, 'chipin/home.html', context)