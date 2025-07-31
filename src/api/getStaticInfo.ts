import { apiInstance } from '.'
import { DictionaryResponse } from '../model'

export const getDictionary = () => 
  apiInstance(DictionaryResponse).get({ path: '/dictionaries' })

export const getIndustries = () => 
  apiInstance(DictionaryResponse).get({ path: '/industries' })