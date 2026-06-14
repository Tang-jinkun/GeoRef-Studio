import { createRouter, createWebHistory } from 'vue-router'

import ErrorView from '@/views/ErrorView.vue'
import ExportView from '@/views/ExportView.vue'
import HomeView from '@/views/HomeView.vue'
import NewProjectView from '@/views/NewProjectView.vue'
import ProjectDetailView from '@/views/ProjectDetailView.vue'
import ResultsView from '@/views/ResultsView.vue'
import TasksView from '@/views/TasksView.vue'
import UploadStatesView from '@/views/UploadStatesView.vue'
import WorkbenchView from '@/views/WorkbenchView.vue'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/projects',
    },
    {
      path: '/projects',
      name: 'projects',
      component: HomeView,
    },
    {
      path: '/projects/new',
      name: 'project-new',
      component: NewProjectView,
    },
    {
      path: '/projects/:id',
      name: 'project-detail',
      component: ProjectDetailView,
    },
    {
      path: '/projects/:id/workbench',
      name: 'project-workbench',
      component: WorkbenchView,
    },
    {
      path: '/projects/:id/export',
      name: 'project-export',
      component: ExportView,
    },
    {
      path: '/projects/:id/results',
      name: 'project-results',
      component: ResultsView,
    },
    {
      path: '/tasks',
      name: 'tasks',
      component: TasksView,
    },
    {
      path: '/upload-states',
      name: 'upload-states',
      component: UploadStatesView,
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: ErrorView,
    },
  ],
})
