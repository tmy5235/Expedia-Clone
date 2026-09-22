async function accountRequest(path, credentials) {
  let response
  try {
    response = await fetch(`/api/${path}`, {
      method: path === 'session' ? 'GET' : 'POST',
      headers: { 'Content-Type': 'application/json' },
      ...(credentials ? { body: JSON.stringify(credentials) } : {}),
    })
  } catch {
    throw new Error('Unable to reach the account service. Please try again.')
  }
  if (response.status === 204) return null
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    const detail = data?.detail
    throw new Error(typeof detail === 'string' ? detail : detail?.[0]?.msg || 'The account request failed.')
  }
  if (path === 'session' && data === null) return null
  if (!data?.user_id || !data?.username) throw new Error('The account service returned an invalid response.')
  return data
}
export const getSession = () => accountRequest('session')
export const createAccount = (credentials) => accountRequest('accounts', credentials)
export const login = (credentials) => accountRequest('login', credentials)
export const logout = () => accountRequest('logout')
