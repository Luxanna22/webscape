// Lesson Comments Manager - Bootstrap UI with Chat-style Layout
// Input at bottom, comments scroll above

class LessonCommentManager {
    constructor(lessonContentId) {
        this.lessonContentId = lessonContentId;
        this.comments = [];
        this.commentContainer = null;
        this.commentsLoaded = false; // Track if comments have been loaded
        this.isLoading = false; // Prevent multiple simultaneous loads
        this.lastLoadedLessonId = null; // Remember which lesson ID is currently rendered
        
        // Wait for DOM to be ready before initializing
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }

    init() {
        this.commentContainer = document.getElementById('lesson-comments-container');
        if (this.commentContainer) {
            // Don't load comments immediately - wait for panel to open
            this.setupCharCounter();
            console.log('[Comments] Initialized, waiting for panel to open');
        } else {
            console.warn('Comment container not found in DOM');
        }
    }

    // Update lesson ID when navigating between pages
    updateLessonId(newLessonId) {
        console.log('[Comments] updateLessonId called:', {
            oldId: this.lessonContentId,
            newId: newLessonId,
            changed: this.lessonContentId !== newLessonId,
            commentsLoaded: this.commentsLoaded
        });
        
        if (this.lessonContentId !== newLessonId) {
            console.log('[Comments] Updating to new page ID:', newLessonId);
            this.lessonContentId = newLessonId;
            this.comments = [];
            this.commentsLoaded = false; // Reset loaded flag
            this.isLoading = false; // Reset loading flag too
            this.lastLoadedLessonId = null;
            console.log('[Comments] Reset state - commentsLoaded=false, isLoading=false');

            let panelOpen = false;
            const panel = document.getElementById('lesson-comments-dropdown');
            if (panel) {
                panelOpen = panel.style.right === '0px';
            }

            if (this.commentContainer) {
                if (panelOpen) {
                    this.commentContainer.innerHTML = `
                        <div class="text-center py-4" style="color: var(--color-text-muted, #8080a0)">
                            <div class="spinner-border spinner-border-sm text-info mb-2" role="status">
                                <span class="visually-hidden">Loading...</span>
                            </div>
                            <p class="mb-0">Loading fresh comments...</p>
                        </div>
                    `;
                } else {
                    this.commentContainer.innerHTML = `
                        <div class="text-center py-4" style="color: var(--color-text-muted, #8080a0)">
                            <i class="fas fa-comments mb-2"></i>
                            <p class="mb-0">Open the comments panel to load messages for this page.</p>
                        </div>
                    `;
                }
            }

            if (panelOpen) {
                console.log('[Comments] Panel already open, loading new page comments immediately');
                this.loadComments();
            } else {
                console.log('[Comments] Comments will reload on next panel open');
            }
        } else {
            console.log('[Comments] Page ID unchanged, skipping reload');
        }
    }

    setupCharCounter() {
        const textarea = document.getElementById('new-comment-textarea');
        if (textarea) {
            textarea.addEventListener('input', (e) => {
                document.getElementById('char-count').textContent = e.target.value.length;
            });
        }
    }

    async loadComments() {
        if (!this.commentContainer) {
            console.error('[Comments] Comment container not found!');
            return;
        }
        
        // Prevent multiple simultaneous API calls
        if (this.isLoading) {
            console.log('[Comments] Already loading, skipping duplicate request');
            return;
        }
        
        this.isLoading = true;
        
        try {
            console.log('[Comments] Fetching comments for lesson:', this.lessonContentId);
            
            // Show loading state
            this.commentContainer.innerHTML = `
                <div class="text-center py-4" style="color: var(--color-text-muted, #8080a0)">
                    <div class="spinner-border spinner-border-sm text-info mb-2" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mb-0">Loading comments...</p>
                </div>
            `;
            
            const response = await fetch(`/api/lessons/${this.lessonContentId}/comments`);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('[Comments] API error:', {
                    status: response.status,
                    statusText: response.statusText,
                    body: errorText
                });
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            console.log('[Comments] API response:', {
                success: data.success,
                commentCount: data.comments ? data.comments.length : 0
            });
            
            if (data.success) {
                this.comments = data.comments;
                this.commentsLoaded = true;
                this.lastLoadedLessonId = this.lessonContentId;
                this.updateBadges();
                this.renderComments();
            } else {
                throw new Error(data.error || 'Unknown error');
            }
        } catch (error) {
            console.error('[Comments] Error loading comments:', error);
            this.commentsLoaded = false; // Reset on error
            this.lastLoadedLessonId = null;
            this.commentContainer.innerHTML = `
                <div class="alert alert-danger m-3" role="alert">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    <strong>Failed to load comments</strong>
                    <br><small>${error.message}</small>
                </div>
            `;
        } finally {
            this.isLoading = false; // Always reset loading flag
        }
    }

    updateBadges() {
        const totalBadge = document.getElementById('comment-total-badge');
        const count = this.comments.length;

        if (totalBadge) {
            totalBadge.textContent = count;
        }
    }

    renderComments() {
        if (!this.commentContainer) return;

        if (this.comments.length === 0) {
            this.commentContainer.innerHTML = `
                <div class="text-center py-5" style="color: #a0a0b0;">
                    <i class="fas fa-comments fa-3x mb-3" style="opacity: 0.4; color: #7e31ef;"></i>
                    <p class="mb-1" style="color: #d0d0e0;">No comments yet</p>
                    <small style="color: #9090a0;">Be the first to start the discussion!</small>
                </div>
            `;
            return;
        }

        let html = '';
        this.comments.forEach((comment) => {
            html += this.renderComment(comment);
        });

        this.commentContainer.innerHTML = html;
    }

    renderComment(comment) {
        const likedClass = comment.liked ? 'text-danger' : '';
        const likedIcon = comment.liked ? 'fas fa-heart' : 'far fa-heart';
        const likedStyle = comment.liked ? 'color: #ff4757;' : 'color: #9090a0;';
        
        return `
            <div class="card mb-3" style="background: rgba(25, 24, 44, 0.8); border: 1px solid rgba(126, 49, 239, 0.3);" id="comment-${comment.id}">
                <div class="card-body p-3">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <div>
                            <h6 class="mb-0" style="color: #a259ff; font-weight: 600;">${this.escapeHtml(comment.username)}</h6>
                            <small style="color: #8080a0; font-size: 0.75rem;">${this.formatTimeAgo(comment.created_at)}</small>
                        </div>
                        ${window.currentUserId === comment.user_id ? `
                            <button class="btn btn-link btn-sm p-0" onclick="window.commentManager.deleteComment(${comment.id})" title="Delete" style="color: #ff4757; text-decoration: none;">
                                <i class="fas fa-trash"></i>
                            </button>
                        ` : ''}
                    </div>
                    
                    <p class="card-text mb-2" style="color: #e0e0e0; white-space: pre-wrap;">${this.escapeHtml(comment.comment_text)}</p>
                    
                    <div class="d-flex gap-3 align-items-center border-top pt-2" style="border-color: rgba(126, 49, 239, 0.2) !important;">
                        <button class="btn btn-link btn-sm p-0" onclick="window.commentManager.likeComment(${comment.id})" data-comment-id="${comment.id}" id="like-btn-${comment.id}" style="${likedStyle} text-decoration: none;">
                            <i class="${likedIcon}" id="like-icon-${comment.id}"></i>
                            <span class="ms-1" id="like-count-${comment.id}">${comment.like_count}</span>
                        </button>
                        <button class="btn btn-link btn-sm p-0" onclick="window.commentManager.toggleReplies(${comment.id})" style="color: #7e31ef; text-decoration: none;">
                            <i class="fas fa-reply"></i>
                            <span class="ms-1">${comment.reply_count}</span>
                        </button>
                        <button class="btn btn-link btn-sm p-0" onclick="window.commentManager.showReplyForm(${comment.id})" style="color: #a259ff; text-decoration: none;">
                            <i class="fas fa-comment-dots"></i> Reply
                        </button>
                    </div>

                    <!-- Reply Form -->
                    <div class="mt-2 collapse" id="reply-form-${comment.id}">
                        <div class="card" style="background: rgba(20, 15, 35, 0.8); border: 1px solid #7e31ef;">
                            <div class="card-body p-2">
                                <textarea 
                                    class="form-control form-control-sm mb-2" 
                                    rows="2"
                                    placeholder="Write a reply..."
                                    maxlength="1000"
                                    id="reply-textarea-${comment.id}"
                                    style="background: rgba(25, 24, 44, 0.8); border: 1px solid #7e31ef; color: #e0e0e0; resize: none;"
                                ></textarea>
                                <div class="d-flex justify-content-between align-items-center">
                                    <small style="color: #8080a0;">
                                        <span id="reply-char-count-${comment.id}">0</span>/1000
                                    </small>
                                    <div>
                                        <button class="btn btn-sm btn-outline-secondary" onclick="window.commentManager.hideReplyForm(${comment.id})">Cancel</button>
                                        <button class="btn btn-sm btn-primary" onclick="window.commentManager.submitReply(${comment.id})" style="background: #7e31ef; border: none;">Reply</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Replies Container -->
                    <div class="collapse mt-2" id="replies-${comment.id}">
                        <div id="replies-list-${comment.id}">
                            ${comment.replies && comment.replies.length > 0 ? this.renderReplies(comment.replies) : ''}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderReplies(replies) {
        let html = '';
        replies.forEach(reply => {
            const likedClass = reply.liked ? 'text-danger' : '';
            const likedIcon = reply.liked ? 'fas fa-heart' : 'far fa-heart';
            const likedStyle = reply.liked ? 'color: #ff4757;' : 'color: #9090a0;';
            
            html += `
                <div class="card ms-3 mb-2" style="background: rgba(40, 30, 60, 0.6); border-left: 3px solid #7e31ef; border-radius: 0 8px 8px 0;" id="reply-${reply.id}">
                    <div class="card-body p-2">
                        <div class="d-flex justify-content-between align-items-start mb-1">
                            <div>
                                <h6 class="mb-0" style="color: #ff66c4; font-size: 0.9rem; font-weight: 600;">${this.escapeHtml(reply.username)}</h6>
                                <small style="color: #8080a0; font-size: 0.75rem;">${this.formatTimeAgo(reply.created_at)}</small>
                            </div>
                            ${window.currentUserId === reply.user_id ? `
                                <button class="btn btn-link btn-sm p-0" onclick="window.commentManager.deleteReply(${reply.id})" title="Delete" style="color: #ff4757; text-decoration: none;">
                                    <i class="fas fa-trash fa-xs"></i>
                                </button>
                            ` : ''}
                        </div>
                        <p class="mb-1" style="color: #d0d0d0; font-size: 0.9rem; white-space: pre-wrap;">${this.escapeHtml(reply.reply_text)}</p>
                        <button class="btn btn-link btn-sm p-0" onclick="window.commentManager.likeReply(${reply.id})" id="like-reply-btn-${reply.id}" style="${likedStyle} text-decoration: none;">
                            <i class="${likedIcon}" id="like-reply-icon-${reply.id}"></i>
                            <span class="ms-1" id="like-reply-count-${reply.id}">${reply.like_count}</span>
                        </button>
                    </div>
                </div>
            `;
        });
        return html;
    }

    showReplyForm(commentId) {
        const formElement = document.getElementById(`reply-form-${commentId}`);
        const bsCollapse = new bootstrap.Collapse(formElement, { toggle: true });
        
        // Setup char counter for this reply form
        setTimeout(() => {
            const textarea = document.getElementById(`reply-textarea-${commentId}`);
            const counter = document.getElementById(`reply-char-count-${commentId}`);
            if (textarea && counter) {
                textarea.addEventListener('input', (e) => {
                    counter.textContent = e.target.value.length;
                });
                textarea.focus();
            }
        }, 100);
    }

    hideReplyForm(commentId) {
        const formElement = document.getElementById(`reply-form-${commentId}`);
        const bsCollapse = bootstrap.Collapse.getInstance(formElement);
        if (bsCollapse) {
            bsCollapse.hide();
        }
        document.getElementById(`reply-textarea-${commentId}`).value = '';
        document.getElementById(`reply-char-count-${commentId}`).textContent = '0';
    }

    toggleReplies(commentId) {
        const repliesElement = document.getElementById(`replies-${commentId}`);
        const bsCollapse = new bootstrap.Collapse(repliesElement, { toggle: true });
    }

    async submitComment() {
        const textarea = document.getElementById('new-comment-textarea');
        const text = textarea.value.trim();

        if (!text) {
            this.showToast('Please write a comment', 'warning');
            return;
        }

        try {
            const response = await fetch(`/api/lessons/${this.lessonContentId}/comments`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ comment_text: text })
            });

            const data = await response.json();
            if (data.success) {
                textarea.value = '';
                document.getElementById('char-count').textContent = '0';
                this.showToast('Comment posted!', 'success');
                this.loadComments();
            } else {
                this.showToast(data.message || 'Failed to post comment', 'danger');
            }
        } catch (error) {
            console.error('Error posting comment:', error);
            this.showToast('Error posting comment', 'danger');
        }
    }

    async submitReply(commentId) {
        const textarea = document.getElementById(`reply-textarea-${commentId}`);
        const text = textarea.value.trim();

        if (!text) {
            this.showToast('Please write a reply', 'warning');
            return;
        }

        try {
            const response = await fetch(`/api/comments/${commentId}/replies`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ reply_text: text })
            });

            const data = await response.json();
            if (data.success) {
                this.showToast('Reply posted!', 'success');
                this.hideReplyForm(commentId);
                this.loadComments();
            } else {
                this.showToast(data.message || 'Failed to post reply', 'danger');
            }
        } catch (error) {
            console.error('Error posting reply:', error);
            this.showToast('Error posting reply', 'danger');
        }
    }

    async deleteComment(commentId) {
        if (!confirm('Delete this comment and all its replies?')) return;

        try {
            const response = await fetch(`/api/comments/${commentId}`, {
                method: 'DELETE'
            });

            const data = await response.json();
            if (data.success) {
                this.showToast('Comment deleted', 'success');
                this.loadComments();
            } else {
                this.showToast(data.message || 'Failed to delete comment', 'danger');
            }
        } catch (error) {
            console.error('Error deleting comment:', error);
            this.showToast('Error deleting comment', 'danger');
        }
    }

    async deleteReply(replyId) {
        if (!confirm('Delete this reply?')) return;

        try {
            const response = await fetch(`/api/replies/${replyId}`, {
                method: 'DELETE'
            });

            const data = await response.json();
            if (data.success) {
                this.showToast('Reply deleted', 'success');
                this.loadComments();
            } else {
                this.showToast(data.message || 'Failed to delete reply', 'danger');
            }
        } catch (error) {
            console.error('Error deleting reply:', error);
            this.showToast('Error deleting reply', 'danger');
        }
    }

    async likeComment(commentId) {
        try {
            const response = await fetch(`/api/comments/${commentId}/like`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            const data = await response.json();
            if (data.success) {
                // Update UI immediately
                const btn = document.getElementById(`like-btn-${commentId}`);
                const icon = document.getElementById(`like-icon-${commentId}`);
                const count = document.getElementById(`like-count-${commentId}`);
                
                if (data.liked) {
                    btn.style.color = '#ff4757';
                    icon.classList.remove('far');
                    icon.classList.add('fas');
                } else {
                    btn.style.color = '#9090a0';
                    icon.classList.remove('fas');
                    icon.classList.add('far');
                }
                
                count.textContent = data.like_count;
            }
        } catch (error) {
            console.error('Error liking comment:', error);
            this.showToast('Error liking comment', 'danger');
        }
    }

    async likeReply(replyId) {
        try {
            const response = await fetch(`/api/replies/${replyId}/like`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            const data = await response.json();
            if (data.success) {
                // Update UI immediately
                const btn = document.getElementById(`like-reply-btn-${replyId}`);
                const icon = document.getElementById(`like-reply-icon-${replyId}`);
                const count = document.getElementById(`like-reply-count-${replyId}`);
                
                if (data.liked) {
                    btn.style.color = '#ff4757';
                    icon.classList.remove('far');
                    icon.classList.add('fas');
                } else {
                    btn.style.color = '#9090a0';
                    icon.classList.remove('fas');
                    icon.classList.add('far');
                }
                
                count.textContent = data.like_count;
            }
        } catch (error) {
            console.error('Error liking reply:', error);
            this.showToast('Error liking reply', 'danger');
        }
    }

    formatTimeAgo(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const seconds = Math.floor((now - date) / 1000);
        
        if (seconds < 60) return 'just now';
        const minutes = Math.floor(seconds / 60);
        if (minutes < 60) return `${minutes}m ago`;
        const hours = Math.floor(minutes / 60);
        if (hours < 24) return `${hours}h ago`;
        const days = Math.floor(hours / 24);
        if (days < 7) return `${days}d ago`;
        const weeks = Math.floor(days / 7);
        if (weeks < 4) return `${weeks}w ago`;
        return date.toLocaleDateString();
    }

    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }

    showToast(message, type = 'info') {
        // Simple toast notification
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} position-fixed top-0 end-0 m-3`;
        toast.style.zIndex = '9999';
        toast.textContent = message;
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }
}

// Initialize when DOM is ready
let commentManager;
document.addEventListener('DOMContentLoaded', function() {
    if (typeof lessonContentId !== 'undefined' && lessonContentId) {
        commentManager = new LessonCommentManager(lessonContentId);
    }
});
