"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { useSchools, useAllTags } from "@/lib/api";
import { MessageSquare, HelpCircle, BarChart3, Code, Lightbulb, BookOpen, X, Plus, ArrowLeft, Sparkles, Shield, Tag, FileText, Loader2 } from "lucide-react";

const postTypes = [
    { key: 'thread', label: 'Thread', icon: MessageSquare, desc: 'Start a discussion' },
    { key: 'question', label: 'Question', icon: HelpCircle, desc: 'Ask the community' },
    { key: 'explanation', label: 'Explanation', icon: BookOpen, desc: 'Explain a concept' },
    { key: 'code_snippet', label: 'Code Snippet', icon: Code, desc: 'Share code' },
    { key: 'tip', label: 'Tip', icon: Lightbulb, desc: 'Quick insight' },
    { key: 'poll', label: 'Poll', icon: BarChart3, desc: 'Gather opinions' },
];

export default function CreatePostForm() {
    const router = useRouter();
    const { user } = useAuth();
    const { schools } = useSchools();
    const [orgId, setOrgId] = useState<number | null>(null);
    const { tags: existingTags } = useAllTags(orgId);

    // Resolve orgId
    useEffect(() => {
        if (schools && schools.length > 0) {
            setOrgId(Number(schools[0].id));
        } else if (user?.id) {
            fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/users/${user.id}/orgs`)
                .then(res => res.ok ? res.json() : [])
                .then(data => setOrgId(data?.length > 0 ? Number(data[0].id) : 1))
                .catch(() => setOrgId(1));
        } else {
            setOrgId(1);
        }
    }, [schools, user?.id]);

    const [postType, setPostType] = useState("thread");
    const [title, setTitle] = useState("");
    const [content, setContent] = useState("");
    const [codeContent, setCodeContent] = useState("");
    const [codingLanguage, setCodingLanguage] = useState("javascript");
    const [selectedTags, setSelectedTags] = useState<string[]>([]);
    const [tagInput, setTagInput] = useState("");
    const [pollOptions, setPollOptions] = useState(["", ""]);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [showTagSuggestions, setShowTagSuggestions] = useState(false);

    // AI states
    const [aiQuality, setAiQuality] = useState<any>(null);
    const [aiLoading, setAiLoading] = useState<string | null>(null); // 'quality' | 'tags' | 'summarize' | null
    const [aiSummary, setAiSummary] = useState<string | null>(null);

    const filteredSuggestions = existingTags
        .filter(t => t.name.toLowerCase().includes(tagInput.toLowerCase()) && !selectedTags.includes(t.name))
        .slice(0, 5);

    const addTag = (name: string) => {
        const trimmed = name.trim();
        if (trimmed && !selectedTags.includes(trimmed)) {
            setSelectedTags([...selectedTags, trimmed]);
        }
        setTagInput("");
        setShowTagSuggestions(false);
    };

    const removeTag = (name: string) => {
        setSelectedTags(selectedTags.filter(t => t !== name));
    };

    const getAiRequestBody = () => ({
        post_type: postType,
        title: title.trim(),
        content_text: content || null,
        code_content: postType === 'code_snippet' ? codeContent : null,
        coding_language: postType === 'code_snippet' ? codingLanguage : null,
        org_id: orgId,
    });

    // AI: Quality Check
    const handleQualityCheck = async () => {
        if (!title.trim()) return;
        setAiLoading('quality');
        setAiQuality(null);
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/network/ai/quality-check`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(getAiRequestBody()),
            });
            if (res.ok) {
                setAiQuality(await res.json());
            }
        } catch (err) {
            console.error('Quality check failed:', err);
        } finally {
            setAiLoading(null);
        }
    };

    // AI: Auto-Tag
    const handleAutoTag = async () => {
        if (!title.trim()) return;
        setAiLoading('tags');
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/network/ai/auto-tag`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(getAiRequestBody()),
            });
            if (res.ok) {
                const data = await res.json();
                const newTags = data.tags.filter((t: string) => !selectedTags.includes(t));
                setSelectedTags([...selectedTags, ...newTags]);
            }
        } catch (err) {
            console.error('Auto-tag failed:', err);
        } finally {
            setAiLoading(null);
        }
    };

    // AI: Summarize
    const handleSummarize = async () => {
        if (!title.trim()) return;
        setAiLoading('summarize');
        setAiSummary(null);
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/network/ai/summarize`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(getAiRequestBody()),
            });
            if (res.ok) {
                const data = await res.json();
                setAiSummary(data.summary);
            }
        } catch (err) {
            console.error('Summarize failed:', err);
        } finally {
            setAiLoading(null);
        }
    };

    const handleSubmit = async () => {
        if (!title.trim() || !user?.id || !orgId) return;
        setIsSubmitting(true);

        try {
            const body: any = {
                org_id: orgId,
                author_id: user.id,
                post_type: postType,
                title: title.trim(),
                tags: selectedTags,
            };

            body.content_text = content || null;

            // All post types can have code snippets
            if (codeContent.trim()) {
                body.code_content = codeContent;
                body.coding_language = codingLanguage;
            }

            if (postType === 'poll') {
                body.poll_options = pollOptions.filter(o => o.trim());
            }

            const res = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/network/posts`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });

            if (res.ok) {
                const post = await res.json();
                router.push(`/network/post/${post.id}`);
            }
        } catch (err) {
            console.error('Error creating post:', err);
        } finally {
            setIsSubmitting(false);
        }
    };

    const qualityTierColors: Record<string, string> = {
        high: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 border-green-300 dark:border-green-700',
        medium: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400 border-yellow-300 dark:border-yellow-700',
        low: 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400 border-orange-300 dark:border-orange-700',
        spam: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 border-red-300 dark:border-red-700',
    };

    return (
        <div className="max-w-3xl mx-auto px-4 sm:px-8 pt-6 pb-12">
            {/* Back button */}
            <button
                onClick={() => router.push('/network')}
                className="flex items-center gap-1 text-sm text-gray-500 hover:text-black dark:hover:text-white mb-6 cursor-pointer"
            >
                <ArrowLeft className="w-4 h-4" />
                Back to Network
            </button>

            <h1 className="text-2xl font-semibold text-black dark:text-white mb-6">Create Post</h1>

            {/* Post type selector */}
            <div className="mb-6">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">Post Type</label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                    {postTypes.map(pt => {
                        const Icon = pt.icon;
                        return (
                            <button
                                key={pt.key}
                                onClick={() => setPostType(pt.key)}
                                className={`flex items-center gap-2 p-3 rounded-lg border cursor-pointer transition-colors ${
                                    postType === pt.key
                                        ? 'border-black dark:border-white bg-gray-50 dark:bg-[#1a1a1a]'
                                        : 'border-gray-200 dark:border-[#35363a] hover:border-gray-400 dark:hover:border-gray-600'
                                }`}
                            >
                                <Icon className="w-4 h-4 flex-shrink-0" />
                                <div className="text-left">
                                    <div className="text-sm font-medium text-black dark:text-white">{pt.label}</div>
                                    <div className="text-[10px] text-gray-500 dark:text-gray-400">{pt.desc}</div>
                                </div>
                            </button>
                        );
                    })}
                </div>
            </div>

            {/* Title */}
            <div className="mb-4">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1 block">Title</label>
                <input
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="What's your post about?"
                    className="w-full text-base p-3 rounded-lg border border-gray-200 dark:border-[#35363a] bg-white dark:bg-[#111111] text-black dark:text-white focus:outline-none focus:ring-1 focus:ring-gray-400"
                />
            </div>

            {/* Content */}
            <div className="mb-4">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1 block">
                    {postType === 'code_snippet' ? 'Description (optional)' : 'Content'}
                </label>
                <textarea
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    placeholder={postType === 'code_snippet' ? 'Explain what this code does...' : postType === 'poll' ? 'Add context to your poll...' : 'Write your post content...'}
                    className="w-full text-sm p-3 rounded-lg border border-gray-200 dark:border-[#35363a] bg-white dark:bg-[#111111] text-black dark:text-white resize-none focus:outline-none focus:ring-1 focus:ring-gray-400"
                    rows={postType === 'code_snippet' ? 3 : 6}
                />
            </div>

            {/* Code snippet — available for ALL post types */}
            <div className="mb-4">
                <div className="flex items-center justify-between mb-1">
                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300 flex items-center gap-1.5">
                        <Code className="w-3.5 h-3.5" />
                        Code Snippet {postType !== 'code_snippet' && <span className="text-xs text-gray-400 font-normal">(optional)</span>}
                    </label>
                    <select
                        value={codingLanguage}
                        onChange={(e) => setCodingLanguage(e.target.value)}
                        className="text-xs bg-gray-100 dark:bg-[#222222] border border-gray-300 dark:border-[#35363a] rounded px-2 py-1 text-black dark:text-white"
                    >
                        <option value="javascript">JavaScript</option>
                        <option value="python">Python</option>
                        <option value="java">Java</option>
                        <option value="typescript">TypeScript</option>
                        <option value="cpp">C++</option>
                        <option value="html">HTML</option>
                        <option value="css">CSS</option>
                        <option value="sql">SQL</option>
                    </select>
                </div>
                <textarea
                    value={codeContent}
                    onChange={(e) => setCodeContent(e.target.value)}
                    placeholder="Paste your code here..."
                    className="w-full text-sm p-3 rounded-lg border font-mono border-gray-200 dark:border-[#35363a] bg-gray-50 dark:bg-[#1a1a1a] text-black dark:text-white resize-none focus:outline-none focus:ring-1 focus:ring-gray-400"
                    rows={postType === 'code_snippet' ? 10 : 4}
                />
            </div>

            {/* Poll options */}
            {postType === 'poll' && (
                <div className="mb-4">
                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">Poll Options</label>
                    {pollOptions.map((opt, i) => (
                        <div key={i} className="flex gap-2 mb-2">
                            <input
                                value={opt}
                                onChange={(e) => {
                                    const updated = [...pollOptions];
                                    updated[i] = e.target.value;
                                    setPollOptions(updated);
                                }}
                                placeholder={`Option ${i + 1}`}
                                className="flex-1 text-sm p-2.5 rounded-lg border border-gray-200 dark:border-[#35363a] bg-white dark:bg-[#111111] text-black dark:text-white focus:outline-none focus:ring-1 focus:ring-gray-400"
                            />
                            {pollOptions.length > 2 && (
                                <button
                                    onClick={() => setPollOptions(pollOptions.filter((_, j) => j !== i))}
                                    className="p-2 text-gray-400 hover:text-red-500 cursor-pointer"
                                >
                                    <X className="w-4 h-4" />
                                </button>
                            )}
                        </div>
                    ))}
                    {pollOptions.length < 6 && (
                        <button
                            onClick={() => setPollOptions([...pollOptions, ""])}
                            className="flex items-center gap-1 text-xs text-gray-500 hover:text-black dark:hover:text-white cursor-pointer mt-1"
                        >
                            <Plus className="w-3 h-3" /> Add option
                        </button>
                    )}
                </div>
            )}

            {/* ═══ AI Tools Panel ═══ */}
            <div className="mb-6 p-4 rounded-lg border border-dashed border-purple-300 dark:border-purple-700 bg-purple-50/50 dark:bg-purple-900/10">
                <div className="flex items-center gap-2 mb-3">
                    <Sparkles className="w-4 h-4 text-purple-500" />
                    <span className="text-sm font-semibold text-purple-700 dark:text-purple-400">AI Assistant</span>
                </div>

                <div className="flex flex-wrap gap-2 mb-3">
                    {/* Quality Check */}
                    <button
                        onClick={handleQualityCheck}
                        disabled={!title.trim() || aiLoading === 'quality'}
                        className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-purple-300 dark:border-purple-700 text-purple-700 dark:text-purple-400 hover:bg-purple-100 dark:hover:bg-purple-900/30 disabled:opacity-50 cursor-pointer transition-colors"
                    >
                        {aiLoading === 'quality' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Shield className="w-3.5 h-3.5" />}
                        Check Quality
                    </button>

                    {/* Auto Tag */}
                    <button
                        onClick={handleAutoTag}
                        disabled={!title.trim() || aiLoading === 'tags'}
                        className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-purple-300 dark:border-purple-700 text-purple-700 dark:text-purple-400 hover:bg-purple-100 dark:hover:bg-purple-900/30 disabled:opacity-50 cursor-pointer transition-colors"
                    >
                        {aiLoading === 'tags' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Tag className="w-3.5 h-3.5" />}
                        Auto-Tag
                    </button>

                    {/* Summarize */}
                    <button
                        onClick={handleSummarize}
                        disabled={!title.trim() || aiLoading === 'summarize'}
                        className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-purple-300 dark:border-purple-700 text-purple-700 dark:text-purple-400 hover:bg-purple-100 dark:hover:bg-purple-900/30 disabled:opacity-50 cursor-pointer transition-colors"
                    >
                        {aiLoading === 'summarize' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <FileText className="w-3.5 h-3.5" />}
                        Generate Summary
                    </button>
                </div>

                {/* Quality Check Result */}
                {aiQuality && (
                    <div className={`p-3 rounded-lg border mb-2 ${qualityTierColors[aiQuality.quality_tier] || qualityTierColors.medium}`}>
                        <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-bold uppercase">Quality: {aiQuality.quality_tier}</span>
                            <span className="text-xs opacity-75">{aiQuality.auto_action}</span>
                        </div>
                        <p className="text-xs mb-2">{aiQuality.reason}</p>
                        {aiQuality.suggestions && aiQuality.suggestions.length > 0 && (
                            <div>
                                <span className="text-[10px] font-semibold uppercase opacity-75">Suggestions:</span>
                                <ul className="text-xs mt-0.5 space-y-0.5">
                                    {aiQuality.suggestions.map((s: string, i: number) => (
                                        <li key={i} className="flex items-start gap-1">
                                            <span className="mt-0.5">•</span>
                                            <span>{s}</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>
                )}

                {/* Summary Result */}
                {aiSummary && (
                    <div className="p-3 rounded-lg border border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400">
                        <span className="text-[10px] font-semibold uppercase opacity-75">AI Summary:</span>
                        <p className="text-xs mt-0.5">{aiSummary}</p>
                    </div>
                )}
            </div>

            {/* Tags */}
            <div className="mb-6 relative">
                <div className="flex items-center justify-between mb-1">
                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Tags</label>
                </div>
                <div className="flex flex-wrap gap-1.5 mb-2">
                    {selectedTags.map(tag => (
                        <span
                            key={tag}
                            className="flex items-center gap-1 text-xs rounded-full px-2.5 py-1 bg-gray-100 dark:bg-[#222222] text-gray-700 dark:text-gray-300"
                        >
                            {tag}
                            <button onClick={() => removeTag(tag)} className="cursor-pointer hover:text-red-500">
                                <X className="w-3 h-3" />
                            </button>
                        </span>
                    ))}
                </div>
                <input
                    value={tagInput}
                    onChange={(e) => { setTagInput(e.target.value); setShowTagSuggestions(true); }}
                    onFocus={() => setShowTagSuggestions(true)}
                    onKeyDown={(e) => {
                        if (e.key === 'Enter' && tagInput.trim()) {
                            e.preventDefault();
                            addTag(tagInput);
                        }
                    }}
                    placeholder="Type a tag and press Enter..."
                    className="w-full text-sm p-2.5 rounded-lg border border-gray-200 dark:border-[#35363a] bg-white dark:bg-[#111111] text-black dark:text-white focus:outline-none focus:ring-1 focus:ring-gray-400"
                />
                {showTagSuggestions && tagInput && filteredSuggestions.length > 0 && (
                    <div className="absolute z-10 mt-1 w-full rounded-lg border border-gray-200 dark:border-[#35363a] bg-white dark:bg-[#111111] shadow-lg">
                        {filteredSuggestions.map(tag => (
                            <button
                                key={tag.id}
                                onClick={() => addTag(tag.name)}
                                className="w-full text-left px-3 py-2 text-sm text-black dark:text-white hover:bg-gray-50 dark:hover:bg-[#1a1a1a] cursor-pointer"
                            >
                                {tag.name}
                                <span className="text-xs text-gray-400 ml-2">{tag.usage_count} posts</span>
                            </button>
                        ))}
                    </div>
                )}
            </div>

            {/* Submit */}
            <div className="flex gap-3">
                <button
                    onClick={handleSubmit}
                    disabled={isSubmitting || !title.trim() || title.trim().length < 5}
                    className="px-6 py-3 text-sm font-medium rounded-lg bg-black dark:bg-white text-white dark:text-black hover:opacity-90 disabled:opacity-50 cursor-pointer"
                >
                    {isSubmitting ? 'Publishing...' : 'Publish Post'}
                </button>
                <button
                    onClick={() => router.push('/network')}
                    className="px-6 py-3 text-sm font-medium rounded-lg text-gray-500 hover:text-black dark:hover:text-white cursor-pointer"
                >
                    Cancel
                </button>
            </div>
        </div>
    );
}
