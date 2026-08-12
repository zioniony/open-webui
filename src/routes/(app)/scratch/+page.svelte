<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { showSidebar } from '$lib/stores';

	const STORAGE_KEY = 'openwebui:scratch-note';
	const i18n = getContext('i18n');

	let content = '';
	let editMode = true;

	onMount(() => {
		try {
			content = localStorage.getItem(STORAGE_KEY) ?? '';
		} catch {
			content = '';
		}
	});

	const submit = () => {
		try {
			localStorage.setItem(STORAGE_KEY, content);
		} catch {
			// 浏览器禁用存储时忽略，仅在当前会话生效
		}
		editMode = false;
	};

	const edit = () => {
		editMode = true;
	};
</script>

<div
	class="flex flex-col w-full h-screen max-h-[100dvh] transition-width duration-200 ease-in-out {$showSidebar
		? 'md:max-w-[calc(100%-var(--sidebar-width))]'
		: ''} max-w-full"
>
	<div class="flex-1 max-h-full overflow-y-auto">
		<div class="mx-auto flex h-full w-full max-w-4xl flex-col px-4 pt-5 pb-6">
			<header class="mb-3 flex items-center justify-between">
				<h1 class="text-lg font-medium text-gray-900 dark:text-gray-100">{$i18n.t('Scratch')}</h1>
				<span class="text-xs text-gray-400 dark:text-gray-500"
					>{$i18n.t('Saved only in this browser')}</span
				>
			</header>

			{#if editMode}
				<textarea
					bind:value={content}
					class="min-h-[55vh] w-full flex-1 resize-none rounded-xl border border-gray-200 bg-white p-4 font-mono text-sm leading-relaxed text-gray-800 shadow-sm outline-none focus:border-gray-400 dark:border-gray-800 dark:bg-gray-900 dark:text-gray-100 dark:focus:border-gray-600"
					placeholder={$i18n.t('Type here...')}
					spellcheck="false"
					aria-label={$i18n.t('Scratch content')}
				></textarea>
			{:else}
				<div
					class="w-full flex-1 overflow-auto rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-800 dark:bg-gray-900"
				>
					{#if content}
						<div
							class="whitespace-pre-wrap break-words font-mono text-sm leading-relaxed text-gray-800 dark:text-gray-100"
							>{content}</div
						>
					{:else}
						<p class="text-sm text-gray-400 dark:text-gray-500">{$i18n.t('Empty')}</p>
					{/if}
				</div>
			{/if}

			<div class="mt-4 flex justify-end">
				<button
					type="button"
					class="rounded-lg bg-gray-900 px-5 py-2 text-sm font-medium text-white transition hover:bg-gray-700 dark:bg-gray-100 dark:text-gray-900 dark:hover:bg-gray-300"
					on:click={editMode ? submit : edit}
				>
					{editMode ? 'Submit' : 'Edit'}
				</button>
			</div>
		</div>
	</div>
</div>
