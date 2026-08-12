<script lang="ts">
	export let className = 'size-4';
	export let strokeWidth = '1.5';
</script>

<!-- 一页折角的纸（文档 + 折叠角 + 文字行） -->
<svg
	class={className}
	aria-hidden="true"
	xmlns="http://www.w3.org/2000/svg"
	viewBox="0 0 24 24"
	stroke-width={strokeWidth}
	fill="none"
>
	<path
		d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"
		stroke="currentColor"
		stroke-linecap="round"
		stroke-linejoin="round"
	/>
	<path
		d="M14 2v4a2 2 0 0 0 2 2h4"
		stroke="currentColor"
		stroke-linecap="round"
		stroke-linejoin="round"
	/>
	<path d="M10 9H8" stroke="currentColor" stroke-linecap="round" />
	<path d="M16 13H8" stroke="currentColor" stroke-linecap="round" />
	<path d="M16 17H8" stroke="currentColor" stroke-linecap="round" />
</svg>
