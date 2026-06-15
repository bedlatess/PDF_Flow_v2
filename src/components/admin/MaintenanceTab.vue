<script setup lang="ts">
import { CircleDot, ClipboardList, RefreshCw, Trash2 } from 'lucide-vue-next'
import type { AdminDiagnostics, AdminMaintenance, AdminOperations } from '@/admin/api'
import AdminActionButton from './AdminActionButton.vue'
import AdminPanel from './AdminPanel.vue'
import AdminSectionHeader from './AdminSectionHeader.vue'
import AdminStateBlock from './AdminStateBlock.vue'

defineProps<{
  maintenance: AdminMaintenance | null
  operations: AdminOperations | null
  diagnostics: AdminDiagnostics | null
  savingKey: string | null
}>()

const emit = defineEmits<{
  refresh: []
  cleanupLive: []
  cleanupTestUsers: []
  cleanupExpiredFiles: []
}>()
</script>

<template>
  <div class="space-y-5">
    <AdminPanel as="section" padding="lg">
      <AdminSectionHeader
        eyebrow="System"
        title="Maintenance"
        description="Refresh counts first. Destructive cleanup only runs from the action cards below and still requires confirmation."
        :icon="CircleDot"
      >
        <template #actions>
          <AdminActionButton
            class="min-h-11 py-3"
            :disabled="savingKey === 'maintenance:refresh'"
            :loading="savingKey === 'maintenance:refresh'"
            @click="emit('refresh')"
          >
            <template #icon>
              <RefreshCw class="h-4 w-4" />
            </template>
            Refresh counts
          </AdminActionButton>
        </template>
      </AdminSectionHeader>

      <AdminStateBlock
        class="mt-5"
        tone="info"
        title="Refresh is read-only"
        description="Refresh counts updates the maintenance view only. Cleanup actions are separate, auditable, and confirmed in-app."
      />

      <div class="mt-5 grid gap-4 md:grid-cols-4">
        <AdminStateBlock tone="warning" compact title="Test accounts" :description="`${maintenance?.test_users_count ?? operations?.test_users ?? 0} removable`">
          smoke / ocr / office / @example.com
        </AdminStateBlock>
        <AdminStateBlock tone="info" compact title="Acceptance feedback" :description="`${maintenance?.live_acceptance_feedback_count ?? 0} closable`">
          Titles starting with live acceptance.
        </AdminStateBlock>
        <AdminStateBlock tone="danger" compact title="Needs attention" :description="`${maintenance?.failed_jobs_count ?? diagnostics?.failed_jobs_count ?? 0} failed jobs`">
          Failed jobs are retained for diagnosis.
        </AdminStateBlock>
        <AdminStateBlock tone="success" compact title="Expired temp files" :description="`${maintenance?.file_retention?.removable_count ?? 0} removable`">
          Uploads, results, and packages under retention policy.
        </AdminStateBlock>
      </div>
    </AdminPanel>

    <section class="grid gap-5 xl:grid-cols-3">
      <AdminPanel as="article">
        <AdminSectionHeader
          eyebrow="Low risk cleanup"
          title="Close acceptance feedback"
          description="Mark live-acceptance feedback as closed. Real user feedback is not deleted."
          :icon="ClipboardList"
        />
        <AdminStateBlock
          class="mt-5"
          tone="info"
          title="Currently closable"
          :description="`${maintenance?.live_acceptance_feedback_count ?? 0} feedback reports`"
        >
          {{
            (maintenance?.live_acceptance_feedback_count ?? 0) === 0
              ? 'Nothing to close right now.'
              : 'The action writes a status change after confirmation.'
          }}
        </AdminStateBlock>
        <AdminActionButton
          class="mt-5 min-h-11 py-3"
          full
          :disabled="
            savingKey === 'feedback:cleanup-live' ||
            (maintenance?.live_acceptance_feedback_count ?? 0) === 0
          "
          :loading="savingKey === 'feedback:cleanup-live'"
          @click="emit('cleanupLive')"
        >
          Close acceptance feedback
        </AdminActionButton>
      </AdminPanel>

      <AdminPanel as="article" tone="danger">
        <AdminSectionHeader
          eyebrow="Critical cleanup"
          title="Delete test accounts"
          description="Delete smoke-, ocr-, office-, and @example.com test accounts. Admins and real user accounts are protected by backend checks."
          :icon="Trash2"
        />
        <AdminStateBlock
          class="mt-5"
          tone="danger"
          title="Currently deletable"
          :description="`${maintenance?.test_users_count ?? operations?.test_users ?? 0} test accounts`"
        >
          {{
            (maintenance?.test_users_count ?? operations?.test_users ?? 0) === 0
              ? 'Nothing to delete right now.'
              : 'Deletion happens only after the confirmation dialog.'
          }}
        </AdminStateBlock>
        <AdminActionButton
          tone="danger"
          class="mt-5 min-h-11 py-3"
          full
          :disabled="
            savingKey === 'maintenance:cleanup-users' ||
            (maintenance?.test_users_count ?? operations?.test_users ?? 0) === 0
          "
          :loading="savingKey === 'maintenance:cleanup-users'"
          @click="emit('cleanupTestUsers')"
        >
          Delete test accounts
        </AdminActionButton>
      </AdminPanel>

      <AdminPanel as="article" tone="success">
        <AdminSectionHeader
          eyebrow="Storage cleanup"
          title="Clean expired temp files"
          description="Remove expired uploads, conversion results, and download packages under the configured upload directory."
          :icon="Trash2"
        />
        <AdminStateBlock
          class="mt-5"
          tone="success"
          title="Currently removable"
          :description="`${maintenance?.file_retention?.removable_count ?? 0} temporary paths`"
        >
          <span class="break-all">{{ maintenance?.file_retention?.upload_dir || 'Upload directory is not available yet.' }}</span>
        </AdminStateBlock>
        <AdminActionButton
          tone="success"
          class="mt-5 min-h-11 py-3"
          full
          :disabled="
            savingKey === 'maintenance:cleanup-files' ||
            (maintenance?.file_retention?.removable_count ?? 0) === 0
          "
          :loading="savingKey === 'maintenance:cleanup-files'"
          @click="emit('cleanupExpiredFiles')"
        >
          Clean expired temp files
        </AdminActionButton>
      </AdminPanel>
    </section>

    <AdminStateBlock
      tone="neutral"
      title="What is retained"
      description="API errors, failed jobs, audit logs, and real user feedback remain available for diagnosis. Temp file content follows the configured retention policy; database task summaries keep only operational clues."
    />
  </div>
</template>
