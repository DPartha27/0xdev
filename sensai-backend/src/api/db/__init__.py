import os
from os.path import exists
from api.utils.db import get_new_db_connection, check_table_exists, set_db_defaults
from api.config import (
    sqlite_db_path,
    chat_history_table_name,
    tasks_table_name,
    questions_table_name,
    cohorts_table_name,
    user_cohorts_table_name,
    milestones_table_name,
    users_table_name,
    organizations_table_name,
    user_organizations_table_name,
    courses_table_name,
    course_cohorts_table_name,
    course_tasks_table_name,
    uncategorized_milestone_name,
    course_milestones_table_name,
    group_role_learner,
    group_role_mentor,
    uncategorized_milestone_color,
    batches_table_name,
    user_batches_table_name,
    task_completions_table_name,
    scorecards_table_name,
    question_scorecards_table_name,
    course_generation_jobs_table_name,
    task_generation_jobs_table_name,
    org_api_keys_table_name,
    code_drafts_table_name,
    integrations_table_name,
    assignment_table_name,
    bq_sync_table_name,
    # Learning Network Platform
    skills_table_name,
    task_skills_table_name,
    user_skills_table_name,
    hubs_table_name,
    hub_members_table_name,
    hub_skills_table_name,
    hub_courses_table_name,
    posts_table_name,
    post_skills_table_name,
    post_tasks_table_name,
    replies_table_name,
    votes_table_name,
    bookmarks_table_name,
    poll_options_table_name,
    poll_votes_table_name,
    reputation_events_table_name,
    user_reputation_table_name,
    endorsements_table_name,
    vote_audit_table_name,
    content_quality_table_name,
    flags_table_name,
)
from api.db.migration import run_migrations


async def create_organizations_table(cursor):
    await cursor.execute(
        f"""CREATE TABLE IF NOT EXISTS {organizations_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                default_logo_color TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                deleted_at DATETIME
            )"""
    )

    await cursor.execute(
        f"""CREATE INDEX idx_org_slug ON {organizations_table_name} (slug)"""
    )


async def create_org_api_keys_table(cursor):
    await cursor.execute(
        f"""CREATE TABLE IF NOT EXISTS {org_api_keys_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,
                hashed_key TEXT NOT NULL UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                deleted_at DATETIME,
                FOREIGN KEY (org_id) REFERENCES {organizations_table_name}(id) ON DELETE CASCADE
            )"""
    )

    await cursor.execute(
        f"""CREATE INDEX idx_org_api_key_org_id ON {org_api_keys_table_name} (org_id)"""
    )

    await cursor.execute(
        f"""CREATE INDEX idx_org_api_key_hashed_key ON {org_api_keys_table_name} (hashed_key)"""
    )


async def create_users_table(cursor):
    await cursor.execute(
        f"""CREATE TABLE IF NOT EXISTS {users_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                first_name TEXT,
                middle_name TEXT,
                last_name TEXT,
                default_dp_color TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                deleted_at DATETIME
            )"""
    )


async def create_user_organizations_table(cursor):
    await cursor.execute(
        f"""CREATE TABLE IF NOT EXISTS {user_organizations_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                org_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                deleted_at DATETIME,
                UNIQUE(user_id, org_id),
                FOREIGN KEY (user_id) REFERENCES {users_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (org_id) REFERENCES {organizations_table_name}(id) ON DELETE CASCADE
            )"""
    )

    await cursor.execute(
        f"""CREATE INDEX idx_user_org_user_id ON {user_organizations_table_name} (user_id)"""
    )

    await cursor.execute(
        f"""CREATE INDEX idx_user_org_org_id ON {user_organizations_table_name} (org_id)"""
    )


async def create_cohort_tables(cursor):
    # Create a table to store cohorts
    await cursor.execute(
        f"""CREATE TABLE IF NOT EXISTS {cohorts_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                org_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                deleted_at DATETIME,
                FOREIGN KEY (org_id) REFERENCES {organizations_table_name}(id) ON DELETE CASCADE
            )"""
    )

    await cursor.execute(
        f"""CREATE INDEX idx_cohort_org_id ON {cohorts_table_name} (org_id)"""
    )

    # Create a table to store users in cohorts
    await cursor.execute(
        f"""CREATE TABLE IF NOT EXISTS {user_cohorts_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                cohort_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                deleted_at DATETIME,
                UNIQUE(user_id, cohort_id),
                FOREIGN KEY (user_id) REFERENCES {users_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (cohort_id) REFERENCES {cohorts_table_name}(id) ON DELETE CASCADE
            )"""
    )

    await cursor.execute(
        f"""CREATE INDEX idx_user_cohort_user_id ON {user_cohorts_table_name} (user_id)"""
    )

    await cursor.execute(
        f"""CREATE INDEX idx_user_cohort_cohort_id ON {user_cohorts_table_name} (cohort_id)"""
    )


async def create_batches_table(cursor):
    await cursor.execute(
        f"""CREATE TABLE IF NOT EXISTS {batches_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                cohort_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                deleted_at DATETIME,
                FOREIGN KEY (cohort_id) REFERENCES {cohorts_table_name}(id) ON DELETE CASCADE
            )"""
    )

    await cursor.execute(
        f"""CREATE INDEX idx_batch_cohort_id ON {batches_table_name} (cohort_id)"""
    )

    await cursor.execute(
        f"""CREATE TABLE IF NOT EXISTS {user_batches_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                batch_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                deleted_at DATETIME,
                UNIQUE(user_id, batch_id),
                FOREIGN KEY (user_id) REFERENCES {users_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (batch_id) REFERENCES {batches_table_name}(id) ON DELETE CASCADE
            )"""
    )

    await cursor.execute(
        f"""CREATE INDEX idx_user_batch_user_id ON {user_batches_table_name} (user_id)"""
    )

    await cursor.execute(
        f"""CREATE INDEX idx_user_batch_batch_id ON {user_batches_table_name} (batch_id)"""
    )


async def create_course_tasks_table(cursor):
    await cursor.execute(
        f"""CREATE TABLE IF NOT EXISTS {course_tasks_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL,
                ordering INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                deleted_at DATETIME,
                milestone_id INTEGER,
                UNIQUE(task_id, course_id),
                FOREIGN KEY (task_id) REFERENCES {tasks_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (course_id) REFERENCES {courses_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (milestone_id) REFERENCES {milestones_table_name}(id) ON DELETE CASCADE
            )"""
    )

    await cursor.execute(
        f"""CREATE INDEX idx_course_task_task_id ON {course_tasks_table_name} (task_id)"""
    )

    await cursor.execute(
        f"""CREATE INDEX idx_course_task_course_id ON {course_tasks_table_name} (course_id)"""
    )

    await cursor.execute(
        f"""CREATE INDEX idx_course_task_milestone_id ON {course_tasks_table_name} (milestone_id)"""
    )


async def create_course_milestones_table(cursor):
    await cursor.execute(
        f"""CREATE TABLE IF NOT EXISTS {course_milestones_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                milestone_id INTEGER,
                ordering INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                deleted_at DATETIME,
                UNIQUE(course_id, milestone_id),
                FOREIGN KEY (course_id) REFERENCES {courses_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (milestone_id) REFERENCES {milestones_table_name}(id) ON DELETE CASCADE
            )"""
    )

    await cursor.execute(
        f"""CREATE INDEX idx_course_milestone_course_id ON {course_milestones_table_name} (course_id)"""
    )

    await cursor.execute(
        f"""CREATE INDEX idx_course_milestone_milestone_id ON {course_milestones_table_name} (milestone_id)"""
    )


async def create_milestones_table(cursor):
    await cursor.execute(
        f"""CREATE TABLE IF NOT EXISTS {milestones_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                color TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                deleted_at DATETIME,
                FOREIGN KEY (org_id) REFERENCES {organizations_table_name}(id) ON DELETE CASCADE
            )"""
    )

    await cursor.execute(
        f"""CREATE INDEX idx_milestone_org_id ON {milestones_table_name} (org_id)"""
    )


async def create_courses_table(cursor):
    await cursor.execute(
        f"""CREATE TABLE IF NOT EXISTS {courses_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                deleted_at DATETIME,
                FOREIGN KEY (org_id) REFERENCES {organizations_table_name}(id) ON DELETE CASCADE
            )"""
    )

    await cursor.execute(
        f"""CREATE INDEX idx_course_org_id ON {courses_table_name} (org_id)"""
    )


async def create_course_cohorts_table(cursor):
    await cursor.execute(
        f"""CREATE TABLE IF NOT EXISTS {course_cohorts_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                cohort_id INTEGER NOT NULL,
                is_drip_enabled BOOLEAN DEFAULT FALSE,
                frequency_value INTEGER,
                frequency_unit TEXT,
                publish_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                deleted_at DATETIME,
                UNIQUE(course_id, cohort_id),
                FOREIGN KEY (course_id) REFERENCES {courses_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (cohort_id) REFERENCES {cohorts_table_name}(id) ON DELETE CASCADE
            )"""
    )

    await cursor.execute(
        f"""CREATE INDEX idx_course_cohort_course_id ON {course_cohorts_table_name} (course_id)"""
    )

    await cursor.execute(
        f"""CREATE INDEX idx_course_cohort_cohort_id ON {course_cohorts_table_name} (cohort_id)"""
    )


async def create_bq_sync_table(cursor):
    await cursor.execute(
        f"""CREATE TABLE IF NOT EXISTS {bq_sync_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                ended_at DATETIME
            )"""
    )

    await cursor.execute(
        f"""CREATE INDEX IF NOT EXISTS idx_bq_sync_started_at ON {bq_sync_table_name} (started_at)"""
    )


async def create_integrations_table(cursor):
    await cursor.execute(
        f"""CREATE TABLE IF NOT EXISTS {integrations_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                integration_type TEXT NOT NULL,
                access_token TEXT NOT NULL,
                refresh_token TEXT,
                expires_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                deleted_at DATETIME,
                UNIQUE(user_id, integration_type),
                FOREIGN KEY (user_id) REFERENCES {users_table_name}(id) ON DELETE CASCADE
            )"""
    )

    await cursor.execute(
        f"""CREATE INDEX IF NOT EXISTS idx_integration_user_id ON {integrations_table_name} (user_id)"""
    )

    await cursor.execute(
        f"""CREATE INDEX IF NOT EXISTS idx_integration_integration_type ON {integrations_table_name} (integration_type)"""
    )

    update_trigger_name = f"set_updated_at_update_{integrations_table_name}"
    await cursor.execute(f"DROP TRIGGER IF EXISTS {update_trigger_name}")
    await cursor.execute(
        f"""
            CREATE TRIGGER {update_trigger_name}
            AFTER UPDATE ON {integrations_table_name}
            FOR EACH ROW
            BEGIN
                UPDATE {integrations_table_name} 
                SET updated_at = CURRENT_TIMESTAMP 
                WHERE rowid = NEW.rowid;
            END
        """
    )


async def create_tasks_table(cursor):
    await cursor.execute(
        f"""CREATE TABLE IF NOT EXISTS {tasks_table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    org_id INTEGER NOT NULL,
                    type TEXT NOT NULL,
                    blocks TEXT,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    deleted_at DATETIME,
                    scheduled_publish_at DATETIME,
                    FOREIGN KEY (org_id) REFERENCES {organizations_table_name}(id) ON DELETE CASCADE
                )"""
    )

    await cursor.execute(
        f"""CREATE INDEX idx_task_org_id ON {tasks_table_name} (org_id)"""
    )


async def create_questions_table(cursor):
    await cursor.execute(
        f"""CREATE TABLE IF NOT EXISTS {questions_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                blocks TEXT,
                answer TEXT,
                input_type TEXT NOT NULL,
                coding_language TEXT,
                generation_model TEXT,
                response_type TEXT NOT NULL,
                position INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                deleted_at DATETIME,
                max_attempts INTEGER,
                is_feedback_shown BOOLEAN NOT NULL,
                context TEXT,
                title TEXT NOT NULL,
                settings JSON,
                FOREIGN KEY (task_id) REFERENCES {tasks_table_name}(id) ON DELETE CASCADE
            )"""
    )

    await cursor.execute(
        f"""CREATE INDEX idx_question_task_id ON {questions_table_name} (task_id)"""
    )


async def create_assignment_table(cursor):
    await cursor.execute(
        f"""CREATE TABLE IF NOT EXISTS {assignment_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL UNIQUE,
                blocks TEXT,
                input_type TEXT NOT NULL,
                response_type TEXT,
                context TEXT,
                evaluation_criteria TEXT,
                max_attempts INTEGER,
                settings TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                deleted_at DATETIME,
                FOREIGN KEY (task_id) REFERENCES {tasks_table_name}(id) ON DELETE CASCADE
            )"""
    )

    await cursor.execute(
        f"""CREATE INDEX IF NOT EXISTS idx_assignment_task_id ON {assignment_table_name} (task_id)"""
    )

    trigger_name = f"set_updated_at_{assignment_table_name}"
    await cursor.execute(f"DROP TRIGGER IF EXISTS {trigger_name}")
    await cursor.execute(
        f"""
        CREATE TRIGGER {trigger_name}
        AFTER UPDATE ON {assignment_table_name}
        FOR EACH ROW
        BEGIN
            UPDATE {assignment_table_name}
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = NEW.id;
        END;
        """
    )


async def create_scorecards_table(cursor):
    await cursor.execute(
        f"""CREATE TABLE IF NOT EXISTS {scorecards_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                criteria TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                deleted_at DATETIME,
                status TEXT,
                FOREIGN KEY (org_id) REFERENCES {organizations_table_name}(id) ON DELETE CASCADE
            )"""
    )

    await cursor.execute(
        f"""CREATE INDEX idx_scorecard_org_id ON {scorecards_table_name} (org_id)"""
    )


async def create_question_scorecards_table(cursor):
    await cursor.execute(
        f"""CREATE TABLE IF NOT EXISTS {question_scorecards_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL,
                scorecard_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                deleted_at DATETIME,
                FOREIGN KEY (question_id) REFERENCES {questions_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (scorecard_id) REFERENCES {scorecards_table_name}(id) ON DELETE CASCADE,
                UNIQUE(question_id, scorecard_id)
            )"""
    )

    await cursor.execute(
        f"""CREATE INDEX idx_question_scorecard_question_id ON {question_scorecards_table_name} (question_id)"""
    )

    await cursor.execute(
        f"""CREATE INDEX idx_question_scorecard_scorecard_id ON {question_scorecards_table_name} (scorecard_id)"""
    )


async def create_chat_history_table(cursor):
    await cursor.execute(
        f"""
                CREATE TABLE IF NOT EXISTS {chat_history_table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    question_id INTEGER,
                    task_id INTEGER,
                    role TEXT NOT NULL,
                    content TEXT,
                    response_type TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    deleted_at DATETIME,
                    FOREIGN KEY (question_id) REFERENCES {questions_table_name}(id),
                    FOREIGN KEY (task_id) REFERENCES {tasks_table_name}(id),
                    FOREIGN KEY (user_id) REFERENCES {users_table_name}(id) ON DELETE CASCADE
                )"""
    )

    await cursor.execute(
        f"""CREATE INDEX idx_chat_history_user_id ON {chat_history_table_name} (user_id)"""
    )

    await cursor.execute(
        f"""CREATE INDEX idx_chat_history_task_id ON {chat_history_table_name} (task_id)"""
    )

    await cursor.execute(
        f"""CREATE INDEX idx_chat_history_question_id ON {chat_history_table_name} (question_id)"""
    )


async def create_task_completion_table(cursor):
    await cursor.execute(
        f"""CREATE TABLE IF NOT EXISTS {task_completions_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                task_id INTEGER,
                question_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                deleted_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES {users_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (task_id) REFERENCES {tasks_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (question_id) REFERENCES {questions_table_name}(id) ON DELETE CASCADE,
                UNIQUE(user_id, task_id),
                UNIQUE(user_id, question_id)
            )"""
    )

    await cursor.execute(
        f"""CREATE INDEX idx_task_completion_user_id ON {task_completions_table_name} (user_id)"""
    )

    await cursor.execute(
        f"""CREATE INDEX idx_task_completion_task_id ON {task_completions_table_name} (task_id)"""
    )

    await cursor.execute(
        f"""CREATE INDEX idx_task_completion_question_id ON {task_completions_table_name} (question_id)"""
    )


async def create_course_generation_jobs_table(cursor):
    await cursor.execute(
        f"""CREATE TABLE IF NOT EXISTS {course_generation_jobs_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uuid TEXT NOT NULL,
                course_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                job_details TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                deleted_at DATETIME,
                FOREIGN KEY (course_id) REFERENCES {courses_table_name}(id) ON DELETE CASCADE
            )"""
    )

    await cursor.execute(
        f"""CREATE INDEX idx_course_generation_job_course_id ON {course_generation_jobs_table_name} (course_id)"""
    )


async def create_task_generation_jobs_table(cursor):
    await cursor.execute(
        f"""CREATE TABLE IF NOT EXISTS {task_generation_jobs_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uuid TEXT NOT NULL,
                task_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                job_details TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                deleted_at DATETIME,
                FOREIGN KEY (task_id) REFERENCES {tasks_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (course_id) REFERENCES {courses_table_name}(id) ON DELETE CASCADE
            )"""
    )

    await cursor.execute(
        f"""CREATE INDEX idx_task_generation_job_task_id ON {task_generation_jobs_table_name} (task_id)"""
    )

    await cursor.execute(
        f"""CREATE INDEX idx_task_generation_job_course_id ON {task_generation_jobs_table_name} (course_id)"""
    )


async def create_code_drafts_table(cursor):
    await cursor.execute(
        f"""CREATE TABLE IF NOT EXISTS {code_drafts_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                code TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                deleted_at DATETIME,
                UNIQUE(user_id, question_id),
                FOREIGN KEY (user_id) REFERENCES {users_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (question_id) REFERENCES {questions_table_name}(id) ON DELETE CASCADE
            )"""
    )

    # Useful indexes for faster lookup
    await cursor.execute(
        f"""CREATE INDEX IF NOT EXISTS idx_code_drafts_user_id ON {code_drafts_table_name} (user_id)"""
    )

    await cursor.execute(
        f"""CREATE INDEX IF NOT EXISTS idx_code_drafts_question_id ON {code_drafts_table_name} (question_id)"""
    )


# ── Phase 1: Skills ────────────────────────────────────────────────────────────

async def create_skills_table(cursor):
    await cursor.execute(
        f"""CREATE TABLE IF NOT EXISTS {skills_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                slug TEXT NOT NULL,
                description TEXT,
                parent_skill_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                deleted_at DATETIME,
                UNIQUE(org_id, slug),
                FOREIGN KEY (org_id) REFERENCES {organizations_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (parent_skill_id) REFERENCES {skills_table_name}(id) ON DELETE SET NULL
            )"""
    )
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_skill_org_id ON {skills_table_name} (org_id)")
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_skill_parent_id ON {skills_table_name} (parent_skill_id)")
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_skill_slug ON {skills_table_name} (slug)")


async def create_task_skills_table(cursor):
    await cursor.execute(
        f"""CREATE TABLE IF NOT EXISTS {task_skills_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                skill_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                deleted_at DATETIME,
                UNIQUE(task_id, skill_id),
                FOREIGN KEY (task_id) REFERENCES {tasks_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (skill_id) REFERENCES {skills_table_name}(id) ON DELETE CASCADE
            )"""
    )
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_task_skill_task_id ON {task_skills_table_name} (task_id)")
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_task_skill_skill_id ON {task_skills_table_name} (skill_id)")


async def create_user_skills_table(cursor):
    await cursor.execute(
        f"""CREATE TABLE IF NOT EXISTS {user_skills_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                skill_id INTEGER NOT NULL,
                proficiency_level INTEGER NOT NULL DEFAULT 0,
                evidence_count INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                deleted_at DATETIME,
                UNIQUE(user_id, skill_id),
                FOREIGN KEY (user_id) REFERENCES {users_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (skill_id) REFERENCES {skills_table_name}(id) ON DELETE CASCADE
            )"""
    )
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_user_skill_user_id ON {user_skills_table_name} (user_id)")
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_user_skill_skill_id ON {user_skills_table_name} (skill_id)")


# ── Phase 2: Hubs ──────────────────────────────────────────────────────────────

async def create_hubs_table(cursor):
    await cursor.execute(
        f"""CREATE TABLE IF NOT EXISTS {hubs_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                slug TEXT NOT NULL,
                description TEXT,
                icon TEXT,
                visibility TEXT NOT NULL DEFAULT 'public',
                created_by INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                deleted_at DATETIME,
                UNIQUE(org_id, slug),
                FOREIGN KEY (org_id) REFERENCES {organizations_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (created_by) REFERENCES {users_table_name}(id) ON DELETE CASCADE
            )"""
    )
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_hub_org_id ON {hubs_table_name} (org_id)")
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_hub_slug ON {hubs_table_name} (slug)")
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_hub_created_by ON {hubs_table_name} (created_by)")


async def create_hub_members_table(cursor):
    await cursor.execute(
        f"""CREATE TABLE IF NOT EXISTS {hub_members_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hub_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL DEFAULT 'member',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                deleted_at DATETIME,
                UNIQUE(hub_id, user_id),
                FOREIGN KEY (hub_id) REFERENCES {hubs_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES {users_table_name}(id) ON DELETE CASCADE
            )"""
    )
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_hub_member_hub_id ON {hub_members_table_name} (hub_id)")
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_hub_member_user_id ON {hub_members_table_name} (user_id)")


async def create_hub_skills_table(cursor):
    await cursor.execute(
        f"""CREATE TABLE IF NOT EXISTS {hub_skills_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hub_id INTEGER NOT NULL,
                skill_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                deleted_at DATETIME,
                UNIQUE(hub_id, skill_id),
                FOREIGN KEY (hub_id) REFERENCES {hubs_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (skill_id) REFERENCES {skills_table_name}(id) ON DELETE CASCADE
            )"""
    )
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_hub_skill_hub_id ON {hub_skills_table_name} (hub_id)")
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_hub_skill_skill_id ON {hub_skills_table_name} (skill_id)")


async def create_hub_courses_table(cursor):
    await cursor.execute(
        f"""CREATE TABLE IF NOT EXISTS {hub_courses_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hub_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                deleted_at DATETIME,
                UNIQUE(hub_id, course_id),
                FOREIGN KEY (hub_id) REFERENCES {hubs_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (course_id) REFERENCES {courses_table_name}(id) ON DELETE CASCADE
            )"""
    )
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_hub_course_hub_id ON {hub_courses_table_name} (hub_id)")
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_hub_course_course_id ON {hub_courses_table_name} (course_id)")


# ── Phase 3: Posts & Content ───────────────────────────────────────────────────

async def create_posts_table(cursor):
    await cursor.execute(
        f"""CREATE TABLE IF NOT EXISTS {posts_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hub_id INTEGER NOT NULL,
                author_id INTEGER NOT NULL,
                post_type TEXT NOT NULL,
                title TEXT NOT NULL,
                blocks TEXT,
                status TEXT NOT NULL DEFAULT 'published',
                lifecycle_status TEXT NOT NULL DEFAULT 'active',
                is_pinned INTEGER DEFAULT 0,
                is_wiki INTEGER DEFAULT 0,
                view_count INTEGER DEFAULT 0,
                upvote_count INTEGER DEFAULT 0,
                downvote_count INTEGER DEFAULT 0,
                reply_count INTEGER DEFAULT 0,
                accepted_reply_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                deleted_at DATETIME,
                FOREIGN KEY (hub_id) REFERENCES {hubs_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (author_id) REFERENCES {users_table_name}(id) ON DELETE CASCADE
            )"""
    )
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_post_hub_id ON {posts_table_name} (hub_id)")
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_post_author_id ON {posts_table_name} (author_id)")
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_post_type ON {posts_table_name} (post_type)")
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_post_status ON {posts_table_name} (status)")
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_post_created_at ON {posts_table_name} (created_at)")
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_post_lifecycle ON {posts_table_name} (lifecycle_status)")


async def create_post_skills_table(cursor):
    await cursor.execute(
        f"""CREATE TABLE IF NOT EXISTS {post_skills_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                skill_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                deleted_at DATETIME,
                UNIQUE(post_id, skill_id),
                FOREIGN KEY (post_id) REFERENCES {posts_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (skill_id) REFERENCES {skills_table_name}(id) ON DELETE CASCADE
            )"""
    )
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_post_skill_post_id ON {post_skills_table_name} (post_id)")
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_post_skill_skill_id ON {post_skills_table_name} (skill_id)")


async def create_post_tasks_table(cursor):
    await cursor.execute(
        f"""CREATE TABLE IF NOT EXISTS {post_tasks_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                task_id INTEGER NOT NULL,
                relation_type TEXT NOT NULL DEFAULT 'related',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                deleted_at DATETIME,
                UNIQUE(post_id, task_id),
                FOREIGN KEY (post_id) REFERENCES {posts_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (task_id) REFERENCES {tasks_table_name}(id) ON DELETE CASCADE
            )"""
    )
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_post_task_post_id ON {post_tasks_table_name} (post_id)")
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_post_task_task_id ON {post_tasks_table_name} (task_id)")


async def create_replies_table(cursor):
    await cursor.execute(
        f"""CREATE TABLE IF NOT EXISTS {replies_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                parent_reply_id INTEGER,
                author_id INTEGER NOT NULL,
                blocks TEXT,
                upvote_count INTEGER DEFAULT 0,
                downvote_count INTEGER DEFAULT 0,
                is_accepted INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                deleted_at DATETIME,
                FOREIGN KEY (post_id) REFERENCES {posts_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (parent_reply_id) REFERENCES {replies_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (author_id) REFERENCES {users_table_name}(id) ON DELETE CASCADE
            )"""
    )
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_reply_post_id ON {replies_table_name} (post_id)")
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_reply_parent_id ON {replies_table_name} (parent_reply_id)")
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_reply_author_id ON {replies_table_name} (author_id)")


async def create_votes_table(cursor):
    await cursor.execute(
        f"""CREATE TABLE IF NOT EXISTS {votes_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                target_type TEXT NOT NULL,
                target_id INTEGER NOT NULL,
                value INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                deleted_at DATETIME,
                UNIQUE(user_id, target_type, target_id),
                FOREIGN KEY (user_id) REFERENCES {users_table_name}(id) ON DELETE CASCADE
            )"""
    )
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_vote_user_id ON {votes_table_name} (user_id)")
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_vote_target ON {votes_table_name} (target_type, target_id)")


async def create_bookmarks_table(cursor):
    await cursor.execute(
        f"""CREATE TABLE IF NOT EXISTS {bookmarks_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                post_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                deleted_at DATETIME,
                UNIQUE(user_id, post_id),
                FOREIGN KEY (user_id) REFERENCES {users_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (post_id) REFERENCES {posts_table_name}(id) ON DELETE CASCADE
            )"""
    )
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_bookmark_user_id ON {bookmarks_table_name} (user_id)")
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_bookmark_post_id ON {bookmarks_table_name} (post_id)")


async def create_poll_options_table(cursor):
    await cursor.execute(
        f"""CREATE TABLE IF NOT EXISTS {poll_options_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                position INTEGER NOT NULL,
                vote_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                deleted_at DATETIME,
                FOREIGN KEY (post_id) REFERENCES {posts_table_name}(id) ON DELETE CASCADE
            )"""
    )
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_poll_option_post_id ON {poll_options_table_name} (post_id)")


async def create_poll_votes_table(cursor):
    await cursor.execute(
        f"""CREATE TABLE IF NOT EXISTS {poll_votes_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                poll_option_id INTEGER NOT NULL,
                post_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                deleted_at DATETIME,
                UNIQUE(user_id, post_id),
                FOREIGN KEY (user_id) REFERENCES {users_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (poll_option_id) REFERENCES {poll_options_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (post_id) REFERENCES {posts_table_name}(id) ON DELETE CASCADE
            )"""
    )
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_poll_vote_user_id ON {poll_votes_table_name} (user_id)")
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_poll_vote_option_id ON {poll_votes_table_name} (poll_option_id)")


# ── Phase 4: Reputation ────────────────────────────────────────────────────────

async def create_reputation_events_table(cursor):
    await cursor.execute(
        f"""CREATE TABLE IF NOT EXISTS {reputation_events_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                org_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                points INTEGER NOT NULL,
                source_type TEXT,
                source_id INTEGER,
                granted_by INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES {users_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (org_id) REFERENCES {organizations_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (granted_by) REFERENCES {users_table_name}(id) ON DELETE SET NULL
            )"""
    )
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_rep_event_user_id ON {reputation_events_table_name} (user_id)")
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_rep_event_org_id ON {reputation_events_table_name} (org_id)")
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_rep_event_created_at ON {reputation_events_table_name} (created_at)")
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_rep_event_type ON {reputation_events_table_name} (event_type)")


async def create_user_reputation_table(cursor):
    await cursor.execute(
        f"""CREATE TABLE IF NOT EXISTS {user_reputation_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                org_id INTEGER NOT NULL,
                total_points INTEGER NOT NULL DEFAULT 0,
                level TEXT NOT NULL DEFAULT 'newcomer',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, org_id),
                FOREIGN KEY (user_id) REFERENCES {users_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (org_id) REFERENCES {organizations_table_name}(id) ON DELETE CASCADE
            )"""
    )
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_user_rep_user_id ON {user_reputation_table_name} (user_id)")
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_user_rep_org_id ON {user_reputation_table_name} (org_id)")
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_user_rep_total_points ON {user_reputation_table_name} (total_points)")


async def create_endorsements_table(cursor):
    await cursor.execute(
        f"""CREATE TABLE IF NOT EXISTS {endorsements_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endorser_id INTEGER NOT NULL,
                reply_id INTEGER NOT NULL,
                skill_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                deleted_at DATETIME,
                UNIQUE(endorser_id, reply_id),
                FOREIGN KEY (endorser_id) REFERENCES {users_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (reply_id) REFERENCES {replies_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (skill_id) REFERENCES {skills_table_name}(id) ON DELETE SET NULL
            )"""
    )
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_endorsement_endorser_id ON {endorsements_table_name} (endorser_id)")
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_endorsement_reply_id ON {endorsements_table_name} (reply_id)")


async def create_vote_audit_table(cursor):
    await cursor.execute(
        f"""CREATE TABLE IF NOT EXISTS {vote_audit_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                voter_id INTEGER NOT NULL,
                recipient_id INTEGER NOT NULL,
                post_id INTEGER,
                reply_id INTEGER,
                vote_type TEXT NOT NULL,
                view_duration_ms INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (voter_id) REFERENCES {users_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (recipient_id) REFERENCES {users_table_name}(id) ON DELETE CASCADE
            )"""
    )
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_vote_audit_voter_id ON {vote_audit_table_name} (voter_id)")
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_vote_audit_recipient_id ON {vote_audit_table_name} (recipient_id)")
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_vote_audit_created_at ON {vote_audit_table_name} (created_at)")


async def create_content_quality_table(cursor):
    await cursor.execute(
        f"""CREATE TABLE IF NOT EXISTS {content_quality_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL UNIQUE,
                clarity_score REAL,
                relevance_score REAL,
                helpfulness_score REAL,
                originality_score REAL,
                composite_score REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES {posts_table_name}(id) ON DELETE CASCADE
            )"""
    )
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_content_quality_post_id ON {content_quality_table_name} (post_id)")


# ── Phase 5: Moderation ────────────────────────────────────────────────────────

async def create_flags_table(cursor):
    await cursor.execute(
        f"""CREATE TABLE IF NOT EXISTS {flags_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reporter_id INTEGER NOT NULL,
                target_type TEXT NOT NULL,
                target_id INTEGER NOT NULL,
                reason TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                reviewed_by INTEGER,
                reviewed_at DATETIME,
                action_taken TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                deleted_at DATETIME,
                FOREIGN KEY (reporter_id) REFERENCES {users_table_name}(id) ON DELETE CASCADE,
                FOREIGN KEY (reviewed_by) REFERENCES {users_table_name}(id) ON DELETE SET NULL
            )"""
    )
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_flag_reporter_id ON {flags_table_name} (reporter_id)")
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_flag_target ON {flags_table_name} (target_type, target_id)")
    await cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_flag_status ON {flags_table_name} (status)")


async def init_db():
    # Ensure the database folder exists
    db_folder = os.path.dirname(sqlite_db_path)
    if not os.path.exists(db_folder):
        os.makedirs(db_folder)

    if not exists(sqlite_db_path):
        # only set the defaults the first time
        set_db_defaults()
    else:
        await run_migrations()
        return

    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()

        try:
            await create_organizations_table(cursor)

            await create_org_api_keys_table(cursor)

            await create_users_table(cursor)

            await create_user_organizations_table(cursor)

            await create_milestones_table(cursor)

            await create_cohort_tables(cursor)

            await create_courses_table(cursor)

            await create_course_cohorts_table(cursor)

            await create_tasks_table(cursor)

            await create_questions_table(cursor)

            await create_scorecards_table(cursor)

            await create_question_scorecards_table(cursor)

            await create_chat_history_table(cursor)

            await create_task_completion_table(cursor)

            await create_course_tasks_table(cursor)

            await create_course_milestones_table(cursor)

            await create_course_generation_jobs_table(cursor)

            await create_task_generation_jobs_table(cursor)

            await create_code_drafts_table(cursor)

            await create_batches_table(cursor)

            await create_integrations_table(cursor)

            await create_assignment_table(cursor)

            await create_bq_sync_table(cursor)

            # ── Learning Network Platform ──────────────────────────────────
            # Phase 1: Skills
            await create_skills_table(cursor)
            await create_task_skills_table(cursor)
            await create_user_skills_table(cursor)

            # Phase 2: Hubs
            await create_hubs_table(cursor)
            await create_hub_members_table(cursor)
            await create_hub_skills_table(cursor)
            await create_hub_courses_table(cursor)

            # Phase 3: Posts & Content
            await create_posts_table(cursor)
            await create_post_skills_table(cursor)
            await create_post_tasks_table(cursor)
            await create_replies_table(cursor)
            await create_votes_table(cursor)
            await create_bookmarks_table(cursor)
            await create_poll_options_table(cursor)
            await create_poll_votes_table(cursor)

            # Phase 4: Reputation
            await create_reputation_events_table(cursor)
            await create_user_reputation_table(cursor)
            await create_endorsements_table(cursor)
            await create_vote_audit_table(cursor)
            await create_content_quality_table(cursor)

            # Phase 5: Moderation
            await create_flags_table(cursor)

            await conn.commit()

        except Exception as exception:
            # delete db
            os.remove(sqlite_db_path)
            raise exception


async def delete_useless_tables():
    from api.config import (
        tags_table_name,
        task_tags_table_name,
        groups_table_name,
        user_groups_table_name,
        badges_table_name,
        task_scoring_criteria_table_name,
        cv_review_usage_table_name,
        tests_table_name,
    )

    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()

        await cursor.execute(f"DROP TABLE IF EXISTS {tags_table_name}")
        await cursor.execute(f"DROP TABLE IF EXISTS {task_tags_table_name}")
        await cursor.execute(f"DROP TABLE IF EXISTS {tests_table_name}")
        await cursor.execute(f"DROP TABLE IF EXISTS {groups_table_name}")
        await cursor.execute(f"DROP TABLE IF EXISTS {user_groups_table_name}")
        await cursor.execute(f"DROP TABLE IF EXISTS {badges_table_name}")
        await cursor.execute(f"DROP TABLE IF EXISTS {task_scoring_criteria_table_name}")
        await cursor.execute(f"DROP TABLE IF EXISTS {cv_review_usage_table_name}")

    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute(f"PRAGMA table_info({user_cohorts_table_name})")
        user_columns = [col[1] for col in await cursor.fetchall()]

        if "joined_at" not in user_columns:
            await cursor.execute(f"DROP TABLE IF EXISTS {user_cohorts_table_name}_temp")
            await cursor.execute(
                f"""
                CREATE TABLE {user_cohorts_table_name}_temp (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    cohort_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, cohort_id),
                    FOREIGN KEY (user_id) REFERENCES {users_table_name}(id) ON DELETE CASCADE,
                    FOREIGN KEY (cohort_id) REFERENCES {cohorts_table_name}(id) ON DELETE CASCADE
                )
            """
            )
            await cursor.execute(
                f"INSERT INTO {user_cohorts_table_name}_temp (id, user_id, cohort_id, role) SELECT id, user_id, cohort_id, role FROM {user_cohorts_table_name}"
            )
            await cursor.execute(f"DROP TABLE {user_cohorts_table_name}")
            await cursor.execute(
                f"ALTER TABLE {user_cohorts_table_name}_temp RENAME TO {user_cohorts_table_name}"
            )

            # Recreate the indexes that were lost during table recreation
            await cursor.execute(
                f"CREATE INDEX idx_user_cohort_user_id ON {user_cohorts_table_name} (user_id)"
            )
            await cursor.execute(
                f"CREATE INDEX idx_user_cohort_cohort_id ON {user_cohorts_table_name} (cohort_id)"
            )

        await cursor.execute(f"PRAGMA table_info({course_cohorts_table_name})")
        course_columns = [col[1] for col in await cursor.fetchall()]

        for col, col_type, default in [
            ("is_drip_enabled", "BOOLEAN", "FALSE"),
            ("frequency_value", "INTEGER", None),
            ("frequency_unit", "TEXT", None),
            ("publish_at", "DATETIME", None),
        ]:
            if col not in course_columns:
                default_str = f" DEFAULT {default}" if default else ""
                await cursor.execute(
                    f"ALTER TABLE {course_cohorts_table_name} ADD COLUMN {col} {col_type}{default_str}"
                )

        await conn.commit()


async def mark_all_task_generation_jobs_as_failed():
    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()

        await cursor.execute(
            f"UPDATE {task_generation_jobs_table_name} SET status = 'failed' WHERE status = 'started'"
        )

        await conn.commit()


async def mark_all_course_generation_jobs_as_failed():
    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()

        await cursor.execute(
            f"UPDATE {course_generation_jobs_table_name} SET status = 'failed' WHERE status = 'pending'"
        )

        await conn.commit()
