import os
from os.path import exists
from api.models import LeaderboardViewType, TaskInputType, TaskAIResponseType, TaskType

if exists("/appdata"):
    data_root_dir = "/appdata"
    root_dir = "/demo"
    log_dir = "/appdata/logs"
else:
    root_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(root_dir)

    data_root_dir = f"{parent_dir}/db"
    log_dir = f"{parent_dir}/logs"

if not exists(data_root_dir):
    os.makedirs(data_root_dir)

if not exists(log_dir):
    os.makedirs(log_dir)


sqlite_db_path = f"{data_root_dir}/db.sqlite"
log_file_path = f"{log_dir}/backend.log"
db_log_file_path = f"{log_dir}/db.log"

chat_history_table_name = "chat_history"
tasks_table_name = "tasks"
questions_table_name = "questions"
blocks_table_name = "blocks"
tests_table_name = "tests"
cohorts_table_name = "cohorts"
course_tasks_table_name = "course_tasks"
course_milestones_table_name = "course_milestones"
courses_table_name = "courses"
course_cohorts_table_name = "course_cohorts"
task_scoring_criteria_table_name = "task_scoring_criteria"
groups_table_name = "groups"
user_cohorts_table_name = "user_cohorts"
user_groups_table_name = "user_groups"
batches_table_name = "batches"
user_batches_table_name = "user_batches"
milestones_table_name = "milestones"
tags_table_name = "tags"
task_tags_table_name = "task_tags"
users_table_name = "users"
badges_table_name = "badges"
cv_review_usage_table_name = "cv_review_usage"
organizations_table_name = "organizations"
user_organizations_table_name = "user_organizations"
task_completions_table_name = "task_completions"
scorecards_table_name = "scorecards"
question_scorecards_table_name = "question_scorecards"
group_role_learner = "learner"
group_role_mentor = "mentor"
course_generation_jobs_table_name = "course_generation_jobs"
task_generation_jobs_table_name = "task_generation_jobs"
org_api_keys_table_name = "org_api_keys"
code_drafts_table_name = "code_drafts"
integrations_table_name = "integrations"
bq_sync_table_name = "bq_sync"
assignment_table_name = "assignment"

# ── Learning Network Platform ──────────────────────────────────────────────────
# Phase 1: Skills
skills_table_name = "skills"
task_skills_table_name = "task_skills"
user_skills_table_name = "user_skills"

# Phase 2: Hubs
hubs_table_name = "hubs"
hub_members_table_name = "hub_members"
hub_skills_table_name = "hub_skills"
hub_courses_table_name = "hub_courses"

# Phase 3: Posts & Content
posts_table_name = "posts"
post_skills_table_name = "post_skills"
post_tasks_table_name = "post_tasks"
replies_table_name = "replies"
votes_table_name = "votes"
bookmarks_table_name = "bookmarks"
poll_options_table_name = "poll_options"
poll_votes_table_name = "poll_votes"

# Phase 4: Reputation
reputation_events_table_name = "reputation_events"
user_reputation_table_name = "user_reputation"
endorsements_table_name = "endorsements"
vote_audit_table_name = "vote_audit"
content_quality_table_name = "content_quality"

# Phase 5: Moderation
flags_table_name = "flags"

# Reputation config
REPUTATION_LEVELS = {
    "newcomer": 0,
    "contributor": 50,
    "active_learner": 100,
    "trusted_member": 300,
    "subject_expert": 750,
    "community_leader": 1500,
}

REPUTATION_POINTS = {
    "post_upvoted": 5,
    "reply_upvoted": 10,
    "post_downvoted": -2,
    "reply_downvoted": -2,
    "answer_accepted": 25,
    "mentor_endorsed": 50,
    "content_removed": -50,
    "downvote_cast": -1,
}

REPUTATION_DAILY_CAP = 200

UPLOAD_FOLDER_NAME = "uploads"

uncategorized_milestone_name = "[UNASSIGNED]"
uncategorized_milestone_color = "#808080"

openai_plan_to_model_name = {
    "reasoning": "o3-mini-2025-01-31",
    "text": "gpt-4.1-2025-04-14",
    "text-mini": "gpt-4.1-mini-2025-04-14",
    "audio": "gpt-4o-audio-preview-2025-06-03",
    "router": "gpt-4.1-mini-2025-04-14",
}
