'use client'
import type { FC } from 'react'
import React from 'react'
import { useContext } from 'use-context-selector'
import s from '../style.module.css'
import type { IChatItem } from '../type'
import MoreInfo from '../more-info'
import AppContext from '@/context/app-context'
import { Markdown } from '@/app/components/base/markdown'

type IQuestionProps = Pick<IChatItem, 'id' | 'content' | 'more' | 'useCurrentUserAvatar'>

const Question: FC<IQuestionProps> = ({ id, content, more, useCurrentUserAvatar }) => {
  const { userProfile } = useContext(AppContext)
  const userName = userProfile?.name
  return (
    <div className='flex items-start justify-end' key={id}>
      <div className={s.questionWrapWrap}>
        <div className={`${s.question} relative text-sm text-gray-900`}>
          <div
            className={'mr-2 py-3 px-4 bg-blue-500 rounded-tl-2xl rounded-b-2xl'}
          >
            <Markdown content={content} />
          </div>
        </div>
        {more && <MoreInfo more={more} isQuestion={true} />}
      </div>
      {useCurrentUserAvatar
        ? (
          <div className='w-10 h-10 shrink-0 leading-10 text-center mr-2 rounded-full bg-primary-600 text-white'>
            {userName?.[0].toLocaleUpperCase()}
          </div>
        )
        : (
          <div className={`${s.questionIcon} w-10 h-10 shrink-0 `}></div>
        )}
    </div>
  )
}
export default React.memo(Question)
