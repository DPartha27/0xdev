export interface PostAuthor {
    id: number;
    first_name: string;
    last_name: string;
    email: string;
    badge_tier: string;
    network_role: 'mentor' | 'newbie' | 'master';
}

export interface NetworkTag {
    id: number;
    name: string;
    slug: string;
    usage_count: number;
    recent_posts?: number;
}

export interface PollOption {
    id: number;
    option_text: string;
    vote_count: number;
    user_voted: boolean;
}

export interface NetworkPost {
    id: number;
    org_id: number;
    author: PostAuthor;
    post_type: 'thread' | 'question' | 'poll' | 'code_snippet' | 'tip' | 'explanation';
    title: string;
    blocks?: any[];
    content_text?: string;
    code_content?: string;
    coding_language?: string;
    status: string;
    is_pinned: boolean;
    view_count: number;
    reply_count: number;
    upvote_count: number;
    downvote_count: number;
    quality_score: number;
    tags: NetworkTag[];
    user_vote?: 'upvote' | 'downvote' | null;
    poll_options?: PollOption[];
    created_at: string;
}

export interface NetworkComment {
    id: number;
    post_id: number;
    author: PostAuthor;
    parent_comment_id?: number;
    content: string;
    code_content?: string;
    coding_language?: string;
    upvote_count: number;
    user_vote?: 'upvote' | null;
    replies?: NetworkComment[];
    created_at: string;
}

export interface UserNetworkProfile {
    user_id: number;
    org_id: number;
    badge_tier: string;
    badge_score: number;
    learning_score: number;
    contribution_score: number;
    endorsement_score: number;
    downvote_penalty: number;
    posts_count: number;
    comments_count: number;
    upvotes_received: number;
    downvotes_received: number;
    network_role: 'mentor' | 'newbie' | 'master';
    last_active_at: string | null;
    first_name: string;
    last_name: string;
    email: string;
}
