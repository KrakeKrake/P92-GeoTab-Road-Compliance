<template>
  <div class="vehicle-tab-scroll">
    <!-- Licence Class -->
    <div class="section-label">Licence Class</div>
    <div class="select-row">
      <div class="sel-wrap">
        <select class="sel" v-model="selectedLicence" @change="onLicenceChange">
          <option value="">— Select licence class —</option>
          <option value="MC">MC — Multi Combination</option>
          <option value="HC">HC — Heavy Combination</option>
          <option value="HR">HR — Heavy Rigid</option>
          <option value="MR">MR — Medium Rigid</option>
          <option value="LR">LR — Light Rigid</option>
        </select>
        <span class="sel-arrow">▾</span>
      </div>
    </div>

    <div v-if="!isLoggedIn" class="info-box">
      <div class="input-unit">
        Guest mode: select a licence class manually to test vehicle validation. 
        Login is only required for saving profile preferences.
      </div>
    </div>

    <!-- Vehicle Profile -->
    <div v-if="selectedLicence" class="section-label">Vehicle Profile</div>
    <div v-if="selectedLicence" class="select-row">
      <div class="sel-wrap">
        <select class="sel" v-model="selectedProfileId" @change="onProfileChange">
          <option value="">— Select vehicle profile —</option>
          <option v-for="profile in profiles" :key="profile.profile_id" :value="profile.profile_id">
            {{ profile.display_name }}
          </option>
        </select>
        <span class="sel-arrow">▾</span>
      </div>
    </div>

    <!-- Axle Configuration -->
    <div v-if="currentProfile" class="section-label">Axle Configuration</div>
    <div v-if="currentProfile" class="select-row">
      <div class="sel-wrap">
        <select class="sel" v-model="selectedAxleConfigId" @change="onAxleChange">
          <option value="">— Select axle configuration —</option>
          <option v-for="config in axleConfigs" :key="config.config_id" :value="config.config_id">
            {{ config.display_name }}
          </option>
        </select>
        <span class="sel-arrow">▾</span>
      </div>
    </div>

    <!-- Mass Scheme Limits -->
    <div v-if="currentAxleConfig" class="section-label">Available Mass Limits</div>

    <div v-if="currentAxleConfig" class="info-box">
      <table class="mass-table">
        <thead>
          <tr>
            <th>Mass Scheme</th>
            <th>Maximum Mass</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>

          <tr v-for="limit in massLimits" :key="limit.mass_scheme_id">
            <td>{{ limit.mass_scheme_id }}</td>
            <td>
              {{ limit.mass_limit_t !== null ? limit.mass_limit_t + ' t' : '—' }}
            </td>
            <td>
              {{ limit.applicable ? 'Applicable' : 'Not applicable' }}
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="currentAxleConfig.note" class="input-unit">
        Note: {{ currentAxleConfig.note }}
      </div>
    </div>

    <!-- Preferred Mass Scheme -->
    <div v-if="currentAxleConfig" class="section-label">
      Preferred Mass Scheme &amp; Operating Mass
    </div>

    <div v-if="currentAxleConfig" class="select-row">
      <div class="sel-wrap">
        <div class="sel-label">Preferred Mass Scheme</div>
        <select class="sel" v-model="selectedMassScheme">
          <option value="">— Select mass scheme —</option>
          <option v-for="limit in applicableMassLimits" :key="limit.mass_scheme_id" :value="limit.mass_scheme_id">
            {{ limit.mass_scheme_id }} — max {{ limit.mass_limit_t }} t
          </option>
        </select>
        <span class="sel-arrow">▾</span>
      </div>
    </div>

    <div v-if="currentAxleConfig" class="input-row">
      <div class="input-wrap">
        <div class="input-label">Operating Mass</div>
        <input class="input-field" v-model.number="operatingMass" type="number" min="0" step="0.1"
          placeholder="e.g. 67" />
        <div class="input-unit">tonnes</div>
      </div>
    </div>

    <!-- Default Dimensions -->
    <div v-if="currentProfile" class="section-label">Default Vehicle Dimensions</div>

    <div v-if="currentProfile" class="info-box">
      <table style="width:100%;font-family:var(--mono);font-size:11px;border-collapse:collapse">
        <tbody>
        <tr>
          <td class="info-key">Width</td>
          <td>{{ currentProfile.default_width_m }} m</td>
        </tr>
        <tr>
          <td class="info-key">Height</td>
          <td>{{ currentProfile.default_height_m }} m</td>
        </tr>
        <tr>
          <td class="info-key">Length</td>
          <td>{{ currentProfile.default_length_m }} m</td>
        </tr>
        </tbody>
      </table>
    </div>

    <!-- Custom Dimensions Option -->
    <div v-if="currentProfile" class="section-label">Custom Dimensions</div>

    <div v-if="currentProfile" class="select-row">
      <div class="sel-wrap">
        <div class="sel-label">Do you want to customise the vehicle dimensions?</div>
        <select class="sel" v-model="useCustomDimensions">
          <option :value="false">No — use default dimensions</option>
          <option :value="true">Yes — enter custom dimensions</option>
        </select>
        <span class="sel-arrow">▾</span>
      </div>
    </div>

    <div v-if="currentProfile && useCustomDimensions">
      <div v-if="dimensionRanges" class="info-box" style="margin-bottom:10px">
        <table style="width:100%;font-family:var(--mono);font-size:11px;border-collapse:collapse">
          <tbody>
          <tr>
            <td class="info-key">Width range</td>
            <td>{{ dimensionRanges.min_width_m }} m – {{ dimensionRanges.max_width_m }} m</td>
          </tr>
          <tr>
            <td class="info-key">Height range</td>
            <td>{{ dimensionRanges.min_height_m }} m – {{ dimensionRanges.max_height_m }} m</td>
          </tr>
          <tr>
            <td class="info-key">Length range</td>
            <td>{{ dimensionRanges.min_length_m }} m – {{ dimensionRanges.max_length_m }} m</td>
          </tr>
          </tbody>
        </table>
      </div>

      <div class="input-row">
        <div class="input-wrap">
          <div class="input-label">Overall Width</div>
          <input class="input-field" v-model.number="customWidth" type="number" :min="dimensionRanges?.min_width_m"
            :max="dimensionRanges?.max_width_m" step="0.1"
            :placeholder="dimensionRanges ? `${dimensionRanges.min_width_m}–${dimensionRanges.max_width_m}` : 'Width'" />
          <div v-if="dimensionRanges" class="input-unit">
            m, allowed {{ dimensionRanges.min_width_m }}–{{ dimensionRanges.max_width_m }}
          </div>
          <div v-else class="input-unit">m</div>
        </div>

        <div class="input-wrap">
          <div class="input-label">Overall Height</div>
          <input class="input-field" v-model.number="customHeight" type="number" :min="dimensionRanges?.min_height_m"
            :max="dimensionRanges?.max_height_m" step="0.1"
            :placeholder="dimensionRanges ? `${dimensionRanges.min_height_m}–${dimensionRanges.max_height_m}` : 'Height'" />
          <div v-if="dimensionRanges" class="input-unit">
            m, allowed {{ dimensionRanges.min_height_m }}–{{ dimensionRanges.max_height_m }}
          </div>
          <div v-else class="input-unit">m</div>
        </div>
      </div>

      <div class="input-row">
        <div class="input-wrap">
          <div class="input-label">Overall Length</div>
          <input class="input-field" v-model.number="customLength" type="number" :min="dimensionRanges?.min_length_m"
            :max="dimensionRanges?.max_length_m" step="0.1"
            :placeholder="dimensionRanges ? `${dimensionRanges.min_length_m}–${dimensionRanges.max_length_m}` : 'Length'" />
          <div v-if="dimensionRanges" class="input-unit">
            m, allowed {{ dimensionRanges.min_length_m }}–{{ dimensionRanges.max_length_m }}
          </div>
          <div v-else class="input-unit">m</div>
        </div>
      </div>
    </div>



    <!-- Extra Template Questions -->
    <div v-if="templateQuestions.length" class="section-label">Additional Questions</div>

    <div v-for="question in templateQuestions" :key="question.name" class="select-row">
      <div class="sel-wrap">
        <div class="sel-label">{{ question.label }}</div>

        <select v-if="question.type === 'bool'" class="sel" v-model="extraAnswers[question.name]">
          <option value="">— Select —</option>
          <option :value="true">True</option>
          <option :value="false">False</option>
        </select>

        <input v-else class="input-field" type="number" step="0.1" v-model.number="extraAnswers[question.name]" />

        <span v-if="question.type === 'bool'" class="sel-arrow">▾</span>
      </div>
    </div>

    <!-- Actions -->
    <button class="cta" @click="classifyAndValidate">
      Classify + Validate Mass
    </button>

    <button class="cta secondary" @click="resetVehicleTab">
      Reset Vehicle Selection
    </button>

    <!-- Result -->
    <div v-if="result" class="section-label">Result</div>

    <div v-if="result" class="info-box">
      <!-- Error result -->
      <div v-if="result.error" class="compliance-result fail">
        <div class="result-icon">!</div>
        <div class="result-body">
          <div class="result-title">ERROR</div>
          <div class="result-detail">{{ result.error }}</div>
        </div>
      </div>

      <!-- Mass result -->
      <div v-if="result.mass_validation_result" class="compliance-result"
        :class="result.mass_validation_result.compliant ? 'pass' : 'fail'">
        <div class="result-icon">
          {{ result.mass_validation_result.compliant ? '✓' : '!' }}
        </div>

        <div class="result-body">
          <div class="result-title">
            {{ result.mass_validation_result.compliant ? 'MASS COMPLIANT' : 'MASS NOT COMPLIANT' }}
          </div>
          <div class="result-detail">
            {{ result.mass_validation_result.reason }}
          </div>
        </div>
      </div>

      <!-- Category / classification result -->
      <div v-if="result.classification_result" class="compliance-result"
        :class="classificationResultClass(result.classification_result.classification)">
        <div class="result-icon">
          {{ classificationResultIcon(result.classification_result.classification) }}
        </div>

        <div class="result-body">
          <div class="result-title">
            Category: {{ formatClassification(result.classification_result.classification) }}
          </div>
          <div class="result-detail">
            {{ result.classification_result.reason }}
          </div>
        </div>
      </div>
    </div>
    <!-- Empty state -->
    <div v-if="!selectedLicence" id="vehiclePlaceholder">
      <div class="empty-state" style="margin-top:12px">
        <div class="empty-state-icon">🚛</div>
        <div class="empty-state-title">{{ isLoggedIn ? 'No vehicle selected' : 'Guest mode' }}</div>
        <div class="empty-state-sub">
          {{ isLoggedIn
            ? 'Your saved licence class determines which vehicle profiles and axle configurations are available.'
            : 'Select a licence class above to test the vehicle validation workflow without logging in.' }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'

const API_BASE = '/api/compliance'

const selectedLicence = ref('')
const selectedProfileId = ref('')
const selectedAxleConfigId = ref('')
const selectedMassScheme = ref('')

const profiles = ref([])
const axleConfigs = ref([])
const templateQuestions = ref([])

const currentProfile = ref(null)
const currentTemplate = ref(null)
const currentAxleConfig = ref(null)

const massLimits = ref([])
const axleConfigDetails = ref(null)
const dimensionRanges = ref(null)

const operatingMass = ref(null)

const useCustomDimensions = ref(false)
const customWidth = ref(null)
const customHeight = ref(null)
const customLength = ref(null)

const extraAnswers = ref({})
const result = ref(null)
const loggedInUser = ref(null)

const profilesCache = ref({})
const vehicleFormDataCache = ref({})

const GUEST_LICENCE_STORAGE_KEY = 'guest_selected_licence_class'

const isLoggedIn = computed(() => {
  return !!loggedInUser.value
})

const applicableMassLimits = computed(() => {
  return massLimits.value.filter((limit) => limit.applicable)
})

async function timedFetchJson(label, url, options = undefined) {
  console.time(label)

  const res = await fetch(url, options)
  const raw = await res.text()

  console.timeEnd(label)

  let data = {}

  try {
    data = raw ? JSON.parse(raw) : {}
  } catch {
    throw new Error(`${label} returned invalid JSON`)
  }

  if (!res.ok) {
    throw new Error(data.detail || `${label} failed`)
  }

  return data
}

async function loadLoggedInUser() {
  const storedUser = localStorage.getItem('user')

  // Guest mode
  if (!storedUser) {
    loggedInUser.value = null

    const savedGuestLicence = sessionStorage.getItem(GUEST_LICENCE_STORAGE_KEY)

    if (savedGuestLicence) {
      selectedLicence.value = savedGuestLicence
      await onLicenceChange()
    }

    return
  }

  try {
    loggedInUser.value = JSON.parse(storedUser)
  } catch {
    loggedInUser.value = null
    return
  }

  if (loggedInUser.value.licence_class_id) {
    selectedLicence.value = loggedInUser.value.licence_class_id

    await onLicenceChange()

    if (loggedInUser.value.favourite_profile_id) {
      const favouriteExists = profiles.value.some(
        (profile) => profile.profile_id === loggedInUser.value.favourite_profile_id
      )

      if (favouriteExists) {
        selectedProfileId.value = loggedInUser.value.favourite_profile_id
        await onProfileChange()
      }
    }
  }
}

onMounted(async () => {
  await loadLoggedInUser()
})

async function onLicenceChange() {
  if (!loggedInUser.value) {
    if (selectedLicence.value) {
      sessionStorage.setItem(GUEST_LICENCE_STORAGE_KEY, selectedLicence.value)
    } else {
      sessionStorage.removeItem(GUEST_LICENCE_STORAGE_KEY)
    }
  }

  resetAfterLicence()

  if (!selectedLicence.value) return

  try {
    if (profilesCache.value[selectedLicence.value]) {
      profiles.value = profilesCache.value[selectedLicence.value]
      return
    }

    const data = await timedFetchJson(
      'VehicleTab: load profiles by licence',
      `${API_BASE}/profiles-by-licence/${selectedLicence.value}`
    )

    const loadedProfiles = Array.isArray(data) ? data : []

    profiles.value = loadedProfiles
    profilesCache.value[selectedLicence.value] = loadedProfiles
  } catch (error) {
    result.value = {
      error: `Failed to load profiles: ${error}`,
    }
  }
}

function resetAfterLicence() {
  selectedProfileId.value = ''
  selectedAxleConfigId.value = ''
  selectedMassScheme.value = ''

  profiles.value = []
  axleConfigs.value = []
  templateQuestions.value = []
  massLimits.value = []

  currentProfile.value = null
  currentTemplate.value = null
  currentAxleConfig.value = null
  axleConfigDetails.value = null
  dimensionRanges.value = null

  operatingMass.value = null

  useCustomDimensions.value = false
  customWidth.value = null
  customHeight.value = null
  customLength.value = null

  extraAnswers.value = {}
  result.value = null
}

async function onProfileChange() {
  selectedAxleConfigId.value = ''
  selectedMassScheme.value = ''

  axleConfigs.value = []
  templateQuestions.value = []
  massLimits.value = []

  currentProfile.value = null
  currentTemplate.value = null
  currentAxleConfig.value = null
  axleConfigDetails.value = null
  dimensionRanges.value = null

  operatingMass.value = null
  useCustomDimensions.value = false
  customWidth.value = null
  customHeight.value = null
  customLength.value = null

  extraAnswers.value = {}
  result.value = null

  if (!selectedProfileId.value) return

  try {
    let data = vehicleFormDataCache.value[selectedProfileId.value]

    if (!data) {
      data = await timedFetchJson(
        'VehicleTab: load vehicle form data',
        `${API_BASE}/vehicle-form-data/${selectedProfileId.value}`
      )

      vehicleFormDataCache.value[selectedProfileId.value] = data
    }

    currentProfile.value = data.profile
    currentTemplate.value = data.template
    dimensionRanges.value = data.dimension_ranges
    axleConfigs.value = data.axle_configurations || []
    templateQuestions.value = data.template?.extra_questions || []
  } catch (error) {
    result.value = {
      error: `Failed to load profile details: ${error}`,
    }
  }
}

async function onAxleChange() {
  currentAxleConfig.value =
    axleConfigs.value.find((config) => config.config_id === selectedAxleConfigId.value) || null

  selectedMassScheme.value = ''
  massLimits.value = []
  axleConfigDetails.value = null
  result.value = null

  if (!currentAxleConfig.value) return

  // No backend call here anymore.
  // Mass limits are already loaded by /vehicle-form-data/<profile_id>.
  axleConfigDetails.value = currentAxleConfig.value
  massLimits.value = currentAxleConfig.value.mass_limits || []
}

function buildAnswers() {
  const answers = {}

  if (useCustomDimensions.value) {
    if (customWidth.value !== null && customWidth.value !== '') {
      answers.overall_width_m = Number(customWidth.value)
    }

    if (customHeight.value !== null && customHeight.value !== '') {
      answers.overall_height_m = Number(customHeight.value)
    }

    if (customLength.value !== null && customLength.value !== '') {
      answers.overall_length_m = Number(customLength.value)
    }
  }

  for (const question of templateQuestions.value) {
    const value = extraAnswers.value[question.name]

    if (value !== '' && value !== undefined && value !== null) {
      answers[question.name] = value
    }
  }

  return answers
}

async function classifyVehicle() {
  const payload = {
    profile_id: currentProfile.value.profile_id,
    axle_config_id: currentAxleConfig.value.config_id,
    custom_dimensions: useCustomDimensions.value,
    answers: buildAnswers(),
  }

  return await timedFetchJson(
    'VehicleTab: classify vehicle',
    `${API_BASE}/classify`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    }
  )
}

async function validateMass() {
  const payload = {
    axle_config_id: currentAxleConfig.value.config_id,
    mass_scheme: selectedMassScheme.value,
    operating_mass_t: Number(operatingMass.value),
  }

  return await timedFetchJson(
    'VehicleTab: validate mass',
    `${API_BASE}/validate-mass`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    }
  )
}

async function classifyAndValidateVehicle() {
  const payload = {
    profile_id: currentProfile.value.profile_id,
    axle_config_id: currentAxleConfig.value.config_id,
    custom_dimensions: useCustomDimensions.value,
    answers: buildAnswers(),
    mass_scheme: selectedMassScheme.value,
    operating_mass_t: Number(operatingMass.value),
  }

  return await timedFetchJson(
    'VehicleTab: classify and validate',
    `${API_BASE}/classify-and-validate`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    }
  )
}

async function classifyAndValidate() {
  if (!selectedLicence.value) {
    result.value = { error: 'Please select a licence class first.' }
    return
  }

  if (!currentProfile.value) {
    result.value = { error: 'Please select a vehicle profile first.' }
    return
  }

  if (!currentAxleConfig.value) {
    result.value = { error: 'Please select an axle configuration first.' }
    return
  }

  if (!selectedMassScheme.value) {
    result.value = { error: 'Please select a mass scheme.' }
    return
  }

  if (!operatingMass.value || Number(operatingMass.value) <= 0) {
    result.value = { error: 'Please enter a valid operating mass in tonnes.' }
    return
  }

  if (useCustomDimensions.value) {
    if (customWidth.value === null || customWidth.value === '') {
      result.value = { error: 'Please enter the overall width.' }
      return
    }

    if (customHeight.value === null || customHeight.value === '') {
      result.value = { error: 'Please enter the overall height.' }
      return
    }

    if (customLength.value === null || customLength.value === '') {
      result.value = { error: 'Please enter the overall length.' }
      return
    }

    if (dimensionRanges.value) {
      if (
        Number(customWidth.value) < dimensionRanges.value.min_width_m ||
        Number(customWidth.value) > dimensionRanges.value.max_width_m
      ) {
        result.value = {
          error: `Width must be between ${dimensionRanges.value.min_width_m} m and ${dimensionRanges.value.max_width_m} m.`,
        }
        return
      }

      if (
        Number(customHeight.value) < dimensionRanges.value.min_height_m ||
        Number(customHeight.value) > dimensionRanges.value.max_height_m
      ) {
        result.value = {
          error: `Height must be between ${dimensionRanges.value.min_height_m} m and ${dimensionRanges.value.max_height_m} m.`,
        }
        return
      }

      if (
        Number(customLength.value) < dimensionRanges.value.min_length_m ||
        Number(customLength.value) > dimensionRanges.value.max_length_m
      ) {
        result.value = {
          error: `Length must be between ${dimensionRanges.value.min_length_m} m and ${dimensionRanges.value.max_length_m} m.`,
        }
        return
      }
    }
  }

  try {
    const combinedResult = await classifyAndValidateVehicle()

    const classificationResult = combinedResult.classification_result
    const massValidationResult = combinedResult.mass_validation_result

    result.value = {
      selected_licence_class: selectedLicence.value,
      selected_profile: currentProfile.value.display_name,
      selected_axle_configuration: currentAxleConfig.value.display_name,
      selected_mass_scheme: selectedMassScheme.value,
      operating_mass_t: Number(operatingMass.value),
      dimensions_used: useCustomDimensions.value
        ? {
            width_m: customWidth.value,
            height_m: customHeight.value,
            length_m: customLength.value,
          }
        : {
            width_m: currentProfile.value.default_width_m,
            height_m: currentProfile.value.default_height_m,
            length_m: currentProfile.value.default_length_m,
          },
      classification_result: classificationResult,
      mass_validation_result: massValidationResult,
    }
  } catch (error) {
    result.value = {
      error: `Failed to classify or validate: ${error}`,
    }
  }
}

function classificationResultClass(classification) {
  if (classification === 'invalid_input') return 'fail'
  if (classification === 'unknown') return 'fail'
  if (classification === 'class_3') return 'warn'

  return 'pass'
}

function classificationResultIcon(classification) {
  if (classification === 'invalid_input') return '✕'
  if (classification === 'unknown') return '✕'
  if (classification === 'class_3') return '!'

  return '✓'
}

function formatClassification(classification) {
  if (classification === 'general_access') return 'General Access'
  if (classification === 'class_2') return 'Class 2'
  if (classification === 'class_3') return 'Class 3'
  if (classification === 'invalid_input') return 'Invalid Input'
  if (classification === 'unknown') return 'Unknown'

  return classification
}

async function resetVehicleTab() {
  const savedLicence = selectedLicence.value

  resetAfterLicence()

  // Logged-in user: restore saved profile if available
  if (loggedInUser.value?.licence_class_id) {
    selectedLicence.value = loggedInUser.value.licence_class_id

    await onLicenceChange()

    if (loggedInUser.value.favourite_profile_id) {
      const favouriteExists = profiles.value.some(
        (profile) => profile.profile_id === loggedInUser.value.favourite_profile_id
      )

      if (favouriteExists) {
        selectedProfileId.value = loggedInUser.value.favourite_profile_id
        await onProfileChange()
      }
    }

    return
  }

  // Guest user: keep selected licence, but clear vehicle/axle/mass selections
  selectedLicence.value = savedLicence

  if (selectedLicence.value) {
    sessionStorage.setItem(GUEST_LICENCE_STORAGE_KEY, selectedLicence.value)
    await onLicenceChange()
  }
}
</script>

<style scoped>
.vehicle-tab-scroll {
  max-height: calc(100vh - 130px);
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 4px;
}
</style>