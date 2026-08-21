<template>
  <main class="admin-page">
    <section class="page-header">
      <div>
        <p class="eyebrow">Admin Management</p>
        <h1>Add New Vehicle Type</h1>
        <p class="subtitle">
          Add a new heavy vehicle profile, dimension rule, axle configuration, and mass limits into the compliance database.
        </p>
      </div>

      <button class="secondary-btn" type="button" @click="resetForm">
        Clear Form
      </button>
    </section>

    <form class="form-stack" @submit.prevent="submitVehicle">
      <!-- Category -->
      <section class="card">
        <div class="card-header">
          <span class="step">1</span>
          <div>
            <h2>Vehicle Category</h2>
            <p>Define the category group this vehicle belongs to.</p>
          </div>
        </div>

        <div class="form-grid">
          <div class="field">
            <label>Category ID</label>
            <input
              v-model="form.category.category_id"
              placeholder="Example: road_train"
            />
          </div>

          <div class="field">
            <label>Category Name</label>
            <input
              v-model="form.category.category_name"
              placeholder="Example: Road Trains"
            />
          </div>
        </div>
      </section>

      <!-- Template -->
      <section class="card">
        <div class="card-header">
          <span class="step">2</span>
          <div>
            <h2>Vehicle Template</h2>
            <p>Create a new template used to group dimension rules and axle configurations.</p>
          </div>
        </div>

        <div class="form-grid">
          <div class="field">
            <label>Template ID</label>
            <input
              v-model="form.template.template_id"
              placeholder="Example: A_DOUBLE"
            />
          </div>

          <div class="field">
            <label>Template Name</label>
            <input
              v-model="form.template.template_name"
              placeholder="Example: A-double"
            />
          </div>

          <div class="field">
            <label>Base Type</label>
            <select v-model="form.template.base_type">
              <option value="" disabled>Select base type</option>
              <option value="rigid">rigid</option>
              <option value="articulated">articulated</option>
              <option value="b_double">b_double</option>
              <option value="road_train">road_train</option>
              <option value="multi_combination">multi_combination</option>
            </select>
          </div>
        </div>
      </section>

      <!-- Profile -->
      <section class="card">
        <div class="card-header">
          <span class="step">3</span>
          <div>
            <h2>Vehicle Profile</h2>
            <p>This controls how the vehicle appears in the Vehicle tab.</p>
          </div>
        </div>

        <div class="form-grid">
          <div class="field">
            <label>Profile ID</label>
            <input
              v-model="form.profile.profile_id"
              placeholder="Example: STANDARD_A_DOUBLE"
            />
          </div>

          <div class="field">
            <label>Display Name</label>
            <input
              v-model="form.profile.display_name"
              placeholder="Example: 9 Axle A-double"
            />
          </div>

          <div class="field">
            <label>Vehicle Family</label>
            <select v-model="form.profile.vehicle_family">
              <option value="" disabled>Select vehicle family</option>
              <option value="rigid_truck">rigid_truck</option>
              <option value="articulated">articulated</option>
              <option value="multi_combination">multi_combination</option>
            </select>
          </div>

          <div class="field">
            <label>Combination Type</label>
            <select v-model="form.profile.combination_type">
              <option value="" disabled>Select combination type</option>
              <option value="single_vehicle">single_vehicle</option>
              <option value="single_trailer">single_trailer</option>
              <option value="multi_trailer">multi_trailer</option>
            </select>
          </div>

          <div class="field">
            <label>GVM Category</label>
            <input
              v-model="form.profile.gvm_category"
              placeholder="Example: multi_combination"
            />
          </div>

          <div class="field">
            <label>Axle Count</label>
            <input
              v-model="form.profile.axle_count"
              type="number"
              min="0"
              placeholder="Example: 9"
            />
          </div>

          <div class="field">
            <label>Required Licence Class</label>
            <select v-model="form.profile.required_licence_class_id">
              <option value="" disabled>Select licence class</option>
              <option value="LR">LR</option>
              <option value="MR">MR</option>
              <option value="HR">HR</option>
              <option value="HC">HC</option>
              <option value="MC">MC</option>
            </select>
          </div>
        </div>

        <div class="checkbox-row">
          <label class="checkbox-field">
            <input type="checkbox" v-model="form.profile.axle_configurable" />
            <span>Axle configurable</span>
          </label>

          <label class="checkbox-field">
            <input type="checkbox" v-model="form.profile.allow_custom_dimensions" />
            <span>Allow custom dimensions</span>
          </label>
        </div>
      </section>

      <!-- Default Dimensions -->
      <section class="card">
        <div class="card-header">
          <span class="step">4</span>
          <div>
            <h2>Default Dimensions</h2>
            <p>These values will auto-fill in the Vehicle tab when this vehicle is selected.</p>
          </div>
        </div>

        <div class="form-grid three">
          <div class="field">
            <label>Default Width (m)</label>
            <input
              v-model="form.profile.default_width_m"
              type="number"
              step="0.01"
              placeholder="Example: 2.50"
            />
          </div>

          <div class="field">
            <label>Default Height (m)</label>
            <input
              v-model="form.profile.default_height_m"
              type="number"
              step="0.01"
              placeholder="Example: 4.30"
            />
          </div>

          <div class="field">
            <label>Default Length (m)</label>
            <input
              v-model="form.profile.default_length_m"
              type="number"
              step="0.01"
              placeholder="Example: 36.50"
            />
          </div>
        </div>
      </section>

      <!-- Dimension Rule -->
      <section class="card">
        <div class="card-header">
          <span class="step">5</span>
          <div>
            <h2>Dimension Compliance Rule</h2>
            <p>These are the legal/prototype limits used by the validation engine.</p>
          </div>
        </div>

        <div class="form-grid">
          <div class="field">
            <label>Rule Name</label>
            <input
              v-model="form.dimension_rule.rule_name"
              placeholder="Example: A-double dimension rule"
            />
          </div>

          <div class="field">
            <label>Classification if Exceeded</label>
            <select v-model="form.dimension_rule.classification_if_exceeded_limit">
              <option value="" disabled>Select classification</option>
              <option value="general_access">general_access</option>
              <option value="class_1">class_1</option>
              <option value="class_2">class_2</option>
              <option value="class_3">class_3</option>
            </select>
          </div>

          <div class="field">
            <label>Width Limit (m)</label>
            <input
              v-model="form.dimension_rule.width_limit_m"
              type="number"
              step="0.01"
              placeholder="Example: 2.50"
            />
          </div>

          <div class="field">
            <label>Height Limit (m)</label>
            <input
              v-model="form.dimension_rule.height_limit_m"
              type="number"
              step="0.01"
              placeholder="Example: 4.30"
            />
          </div>

          <div class="field">
            <label>Length Limit (m)</label>
            <input
              v-model="form.dimension_rule.length_limit_m"
              type="number"
              step="0.01"
              placeholder="Example: 36.50"
            />
          </div>

          <div class="field full">
            <label>Rule Note</label>
            <textarea
              v-model="form.dimension_rule.note"
              placeholder="Example: Type 1 road train dimension rule."
            ></textarea>
          </div>
        </div>
      </section>

      <!-- Input Sanity Range -->
      <section class="card">
        <div class="card-header">
          <span class="step">6</span>
          <div>
            <h2>Input Sanity Range</h2>
            <p>Controls the minimum and maximum values users can enter in the form.</p>
          </div>
        </div>

        <div class="form-grid three">
          <div class="field">
            <label>Min Width (m)</label>
            <input
              v-model="form.input_sanity_range.min_width_m"
              type="number"
              step="0.01"
              placeholder="Example: 2.00"
            />
          </div>

          <div class="field">
            <label>Max Width (m)</label>
            <input
              v-model="form.input_sanity_range.max_width_m"
              type="number"
              step="0.01"
              placeholder="Example: 3.00"
            />
          </div>

          <div class="field">
            <label>Min Height (m)</label>
            <input
              v-model="form.input_sanity_range.min_height_m"
              type="number"
              step="0.01"
              placeholder="Example: 2.50"
            />
          </div>

          <div class="field">
            <label>Max Height (m)</label>
            <input
              v-model="form.input_sanity_range.max_height_m"
              type="number"
              step="0.01"
              placeholder="Example: 5.00"
            />
          </div>

          <div class="field">
            <label>Min Length (m)</label>
            <input
              v-model="form.input_sanity_range.min_length_m"
              type="number"
              step="0.01"
              placeholder="Example: 20.00"
            />
          </div>

          <div class="field">
            <label>Max Length (m)</label>
            <input
              v-model="form.input_sanity_range.max_length_m"
              type="number"
              step="0.01"
              placeholder="Example: 40.00"
            />
          </div>
        </div>
      </section>

      <!-- Axle Configurations -->
      <section class="card">
        <div class="card-header with-action">
          <div class="card-title-row">
            <span class="step">7</span>
            <div>
              <h2>Axle Configurations</h2>
              <p>Add one or more axle configurations and mass limits.</p>
            </div>
          </div>

          <button class="secondary-btn" type="button" @click="addAxleConfig">
            + Add Axle Config
          </button>
        </div>

        <div v-if="form.axle_configurations.length === 0" class="empty-state">
          No axle configuration added yet. Click “Add Axle Config” to begin.
        </div>

        <div
          v-for="(config, index) in form.axle_configurations"
          :key="index"
          class="axle-card"
        >
          <div class="axle-header">
            <h3>Axle Configuration {{ index + 1 }}</h3>
            <button class="danger-btn" type="button" @click="removeAxleConfig(index)">
              Remove
            </button>
          </div>

          <div class="form-grid">
            <div class="field">
              <label>Axle Config ID</label>
              <input
                v-model="config.axle_config_id"
                placeholder="Example: A_DOUBLE_9_AXLE_6_16_5_16_5_16_5_16_5"
              />
            </div>

            <div class="field">
              <label>Display Name</label>
              <input
                v-model="config.display_name"
                placeholder="Example: 9 Axle A-double"
              />
            </div>

            <div class="field">
              <label>Max Length (m)</label>
              <input
                v-model="config.max_length_m"
                type="number"
                step="0.01"
                placeholder="Example: 36.50"
              />
            </div>

            <div class="field">
              <label>Access Path</label>
              <select v-model="config.access_path">
                <option value="" disabled>Select access path</option>
                <option value="general_access">general_access</option>
                <option value="class_1">class_1</option>
                <option value="class_2">class_2</option>
                <option value="class_3">class_3</option>
              </select>
            </div>

            <div class="field full">
              <label>Axle Group Masses (tonnes)</label>
              <input
                v-model="config.axle_group_masses_csv"
                placeholder="Example: 6, 16.5, 16.5, 16.5, 16.5"
              />
              <small>Separate each axle group mass using commas.</small>
            </div>

            <div class="field">
              <label>GML Mass Limit (t)</label>
              <input
                v-model="config.gml_mass_t"
                type="number"
                step="0.01"
                placeholder="Example: 72.00"
              />
            </div>

            <div class="field">
              <label>CML Mass Limit (t)</label>
              <input
                v-model="config.cml_mass_t"
                type="number"
                step="0.01"
                placeholder="Leave blank if not applicable"
              />
            </div>

            <div class="field">
              <label>HML Mass Limit (t)</label>
              <input
                v-model="config.hml_mass_t"
                type="number"
                step="0.01"
                placeholder="Leave blank if not applicable"
              />
            </div>

            <div class="field full">
              <label>Axle Config Note</label>
              <textarea
                v-model="config.note"
                placeholder="Example: Common Type 1 Road Train."
              ></textarea>
            </div>
          </div>
        </div>
      </section>

      <section class="action-card">
        <div>
          <h2>Save New Vehicle</h2>
          <p>The new vehicle will be inserted into the database and should appear in the Vehicle tab after refresh.</p>
        </div>

        <button class="primary-btn" type="submit" :disabled="saving">
          {{ saving ? 'Saving...' : 'Save Vehicle' }}
        </button>
      </section>

      <div v-if="message" class="message success">
        {{ message }}
      </div>

      <div v-if="error" class="message error">
        {{ error }}
      </div>
    </form>
  </main>
</template>

<script setup>
import { ref } from 'vue'

const API_BASE = '/api/compliance'

const saving = ref(false)
const message = ref('')
const error = ref('')

function createEmptyForm() {
  return {
    category: {
      category_id: '',
      category_name: '',
    },
    template: {
      template_id: '',
      template_name: '',
      base_type: '',
    },
    profile: {
      profile_id: '',
      display_name: '',
      vehicle_family: '',
      combination_type: '',
      gvm_category: '',
      axle_count: '',
      axle_configurable: true,
      default_width_m: '',
      default_height_m: '',
      default_length_m: '',
      allow_custom_dimensions: true,
      required_licence_class_id: '',
    },
    dimension_rule: {
      rule_name: '',
      width_limit_m: '',
      height_limit_m: '',
      length_limit_m: '',
      classification_if_exceeded_limit: '',
      note: '',
    },
    input_sanity_range: {
      min_width_m: '',
      max_width_m: '',
      min_height_m: '',
      max_height_m: '',
      min_length_m: '',
      max_length_m: '',
    },
    axle_configurations: [],
  }
}

function createEmptyAxleConfig() {
  return {
    axle_config_id: '',
    display_name: '',
    max_length_m: '',
    access_path: '',
    axle_group_masses_csv: '',
    gml_mass_t: '',
    cml_mass_t: '',
    hml_mass_t: '',
    note: '',
  }
}

const form = ref(createEmptyForm())

function addAxleConfig() {
  form.value.axle_configurations.push(createEmptyAxleConfig())
}

function removeAxleConfig(index) {
  form.value.axle_configurations.splice(index, 1)
}

function resetForm() {
  form.value = createEmptyForm()
  message.value = ''
  error.value = ''
}

function parseRequiredNumber(value) {
  if (value === '' || value === null || value === undefined) return ''
  return Number(value)
}

function parseNullableNumber(value) {
  if (value === '' || value === null || value === undefined) return null
  return Number(value)
}

function parseAxleGroupMasses(csvValue) {
  if (!csvValue) return []

  return String(csvValue)
    .split(',')
    .map((value) => value.trim())
    .filter(Boolean)
    .map(Number)
}

function buildPayload() {
  return {
    category: {
      category_id: form.value.category.category_id,
      category_name: form.value.category.category_name,
    },
    template: {
      template_id: form.value.template.template_id,
      template_name: form.value.template.template_name,
      base_type: form.value.template.base_type,
    },
    profile: {
      profile_id: form.value.profile.profile_id,
      display_name: form.value.profile.display_name,
      vehicle_family: form.value.profile.vehicle_family,
      combination_type: form.value.profile.combination_type,
      gvm_category: form.value.profile.gvm_category,
      axle_count: parseNullableNumber(form.value.profile.axle_count),
      axle_configurable: form.value.profile.axle_configurable,
      default_width_m: parseRequiredNumber(form.value.profile.default_width_m),
      default_height_m: parseRequiredNumber(form.value.profile.default_height_m),
      default_length_m: parseRequiredNumber(form.value.profile.default_length_m),
      allow_custom_dimensions: form.value.profile.allow_custom_dimensions,
      required_licence_class_id: form.value.profile.required_licence_class_id,
    },
    dimension_rule: {
      rule_name: form.value.dimension_rule.rule_name,
      width_limit_m: parseRequiredNumber(form.value.dimension_rule.width_limit_m),
      height_limit_m: parseRequiredNumber(form.value.dimension_rule.height_limit_m),
      length_limit_m: parseRequiredNumber(form.value.dimension_rule.length_limit_m),
      classification_if_exceeded_limit: form.value.dimension_rule.classification_if_exceeded_limit,
      note: form.value.dimension_rule.note,
    },
    input_sanity_range: {
      min_width_m: parseRequiredNumber(form.value.input_sanity_range.min_width_m),
      max_width_m: parseRequiredNumber(form.value.input_sanity_range.max_width_m),
      min_height_m: parseRequiredNumber(form.value.input_sanity_range.min_height_m),
      max_height_m: parseRequiredNumber(form.value.input_sanity_range.max_height_m),
      min_length_m: parseRequiredNumber(form.value.input_sanity_range.min_length_m),
      max_length_m: parseRequiredNumber(form.value.input_sanity_range.max_length_m),
    },
    axle_configurations: form.value.axle_configurations.map((config) => ({
      axle_config_id: config.axle_config_id,
      display_name: config.display_name,
      max_length_m: parseRequiredNumber(config.max_length_m),
      access_path: config.access_path,
      axle_group_masses_t: parseAxleGroupMasses(config.axle_group_masses_csv),
      gml_mass_t: parseNullableNumber(config.gml_mass_t),
      cml_mass_t: parseNullableNumber(config.cml_mass_t),
      hml_mass_t: parseNullableNumber(config.hml_mass_t),
      note: config.note,
    })),
  }
}

async function submitVehicle() {
  message.value = ''
  error.value = ''
  saving.value = true

  try {
    const response = await fetch(`${API_BASE}/admin/vehicles`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(buildPayload()),
    })

    const data = await response.json()

    if (!response.ok) {
      error.value = data.detail || 'Failed to add vehicle.'
      return
    }

    message.value = `${data.message} Profile ID: ${data.profile_id}`
  } catch (err) {
    error.value = `Failed to add vehicle: ${err}`
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
:global(html),
:global(body),
:global(#app) {
  height: 100%;
  overflow: hidden;
}

.admin-page {
  height: 100vh;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 32px;
  box-sizing: border-box;
  background: #f5f7fb;
  color: #172033;
  font-family: Arial, Helvetica, sans-serif;
}

.page-header {
  max-width: 1100px;
  margin: 0 auto 24px;
  padding: 24px;
  border-radius: 18px;
  background: #ffffff;
  border: 1px solid #e5e9f2;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: flex-start;
}

.eyebrow {
  margin: 0 0 6px;
  font-size: 13px;
  font-weight: 700;
  color: #2f6fec;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

h1,
h2,
h3,
p {
  margin-top: 0;
  color: #0a1d44;
}

h1 {
  margin-bottom: 8px;
  font-size: 30px;
}

h2 {
  margin-bottom: 4px;
  font-size: 20px;
}

h3 {
  margin-bottom: 0;
  font-size: 16px;
}

.subtitle,
.card-header p,
.action-card p {
  margin-bottom: 0;
  color: #657089;
  line-height: 1.5;
}

.form-stack {
  max-width: 1100px;
  margin: 0 auto;
}

.card,
.action-card {
  background: #ffffff;
  border: 1px solid #e5e9f2;
  border-radius: 18px;
  padding: 22px;
  margin-bottom: 18px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
}

.card-header,
.card-title-row {
  display: flex;
  align-items: flex-start;
  gap: 14px;
}

.card-header {
  margin-bottom: 18px;
}

.card-header.with-action {
  justify-content: space-between;
  gap: 20px;
}

.step {
  width: 32px;
  height: 32px;
  border-radius: 999px;
  background: #2f6fec;
  color: #ffffff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  flex: 0 0 auto;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.form-grid.three {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.field.full {
  grid-column: 1 / -1;
}

.field label {
  display: block;
  margin-bottom: 7px;
  font-size: 14px;
  font-weight: 700;
  color: #26344d;
}

input,
select,
textarea {
  width: 100%;
  box-sizing: border-box;
  border: 1px solid #d7deea;
  border-radius: 10px;
  padding: 11px 12px;
  font-size: 14px;
  color: #172033;
  background: #ffffff;
  outline: none;
}

input:focus,
select:focus,
textarea:focus {
  border-color: #2f6fec;
  box-shadow: 0 0 0 3px rgba(47, 111, 236, 0.12);
}

textarea {
  min-height: 90px;
  resize: vertical;
}

small {
  display: block;
  margin-top: 6px;
  color: #7a8498;
}

.checkbox-row {
  display: flex;
  gap: 18px;
  margin-top: 18px;
  flex-wrap: wrap;
}

.checkbox-field {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #26344d;
  font-weight: 600;
}

.checkbox-field input {
  width: auto;
}

.axle-card {
  border: 1px dashed #b8c3d6;
  border-radius: 14px;
  padding: 18px;
  margin-top: 14px;
  background: #fbfcff;
}

.axle-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.empty-state {
  padding: 18px;
  border-radius: 14px;
  background: #f7f9fd;
  border: 1px dashed #c8d2e3;
  color: #657089;
  text-align: center;
}

.action-card {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: center;
}

.primary-btn,
.secondary-btn,
.danger-btn {
  border: none;
  border-radius: 10px;
  padding: 11px 16px;
  font-weight: 700;
  cursor: pointer;
  white-space: nowrap;
}

.primary-btn {
  background: #2f6fec;
  color: #ffffff;
}

.primary-btn:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.secondary-btn {
  background: #eef4ff;
  color: #2f6fec;
}

.danger-btn {
  background: #fff0f0;
  color: #c62828;
}

.message {
  padding: 14px 16px;
  border-radius: 12px;
  margin-bottom: 20px;
  font-weight: 600;
}

.message.success {
  background: #eaf8ef;
  color: #176b35;
  border: 1px solid #bde7ca;
}

.message.error {
  background: #fff0f0;
  color: #9b1c1c;
  border: 1px solid #ffc9c9;
}

@media (max-width: 800px) {
  .admin-page {
    padding: 18px;
  }

  .page-header,
  .action-card,
  .card-header.with-action {
    flex-direction: column;
  }

  .form-grid,
  .form-grid.three {
    grid-template-columns: 1fr;
  }
}
</style>