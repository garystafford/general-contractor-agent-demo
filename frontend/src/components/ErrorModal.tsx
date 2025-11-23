import { Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { AlertCircle, XCircle } from 'lucide-react';

export interface ErrorDetail {
  type: 'missing_info' | 'configuration' | 'stuck_state';
  title: string;
  message: string;
  missingFields?: string[];
  blockedTasks?: string[];
  suggestions?: string[];
}

interface ErrorModalProps {
  isOpen: boolean;
  onClose: () => void;
  error: ErrorDetail | null;
  onReset?: () => void;
  onEdit?: () => void;
}

export default function ErrorModal({ isOpen, onClose, error, onReset, onEdit }: ErrorModalProps) {
  if (!error) return null;

  const getIcon = () => {
    switch (error.type) {
      case 'missing_info':
        return <AlertCircle className="h-12 w-12 text-yellow-500" />;
      case 'configuration':
      case 'stuck_state':
        return <XCircle className="h-12 w-12 text-red-500" />;
      default:
        return <AlertCircle className="h-12 w-12 text-yellow-500" />;
    }
  };

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black bg-opacity-50" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-md transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl transition-all">
                <div className="flex flex-col items-center">
                  {getIcon()}

                  <Dialog.Title
                    as="h3"
                    className="mt-4 text-xl font-semibold leading-6 text-gray-900 text-center"
                  >
                    {error.title}
                  </Dialog.Title>

                  <div className="mt-4 w-full">
                    <p className="text-sm text-gray-600 text-center">
                      {error.message}
                    </p>

                    {error.missingFields && error.missingFields.length > 0 && (
                      <div className="mt-4 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                        <p className="text-sm font-medium text-yellow-900 mb-2">
                          Missing Required Information:
                        </p>
                        <ul className="list-disc list-inside space-y-1">
                          {error.missingFields.map((field, index) => (
                            <li key={index} className="text-sm text-yellow-800">
                              {field}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {error.blockedTasks && error.blockedTasks.length > 0 && (
                      <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
                        <p className="text-sm font-medium text-red-900 mb-2">
                          Blocked Tasks:
                        </p>
                        <ul className="list-disc list-inside space-y-1">
                          {error.blockedTasks.map((task, index) => (
                            <li key={index} className="text-sm text-red-800">
                              {task}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {error.suggestions && error.suggestions.length > 0 && (
                      <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <p className="text-sm font-medium text-blue-900 mb-2">
                          Suggestions:
                        </p>
                        <ul className="list-disc list-inside space-y-1">
                          {error.suggestions.map((suggestion, index) => (
                            <li key={index} className="text-sm text-blue-800">
                              {suggestion}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>

                  <div className="mt-6 flex gap-3 w-full">
                    {onEdit && error.type === 'missing_info' && (
                      <button
                        type="button"
                        className="flex-1 inline-flex justify-center rounded-md border border-transparent bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
                        onClick={() => {
                          onEdit();
                          onClose();
                        }}
                      >
                        Edit Description
                      </button>
                    )}

                    {onReset && (error.type === 'stuck_state' || error.type === 'configuration') && (
                      <button
                        type="button"
                        className="flex-1 inline-flex justify-center rounded-md border border-transparent bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-red-500 focus-visible:ring-offset-2"
                        onClick={() => {
                          onReset();
                          onClose();
                        }}
                      >
                        Reset Project
                      </button>
                    )}

                    <button
                      type="button"
                      className="flex-1 inline-flex justify-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
                      onClick={onClose}
                    >
                      {error.type === 'missing_info' ? 'Cancel' : 'Close'}
                    </button>
                  </div>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
}
