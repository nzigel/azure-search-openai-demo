import { Example } from "./Example";

import styles from "./Example.module.css";

export type ExampleModel = {
    text: string;
    value: string;
};

const EXAMPLES: ExampleModel[] = [
    {
        text: "What is the key difference between the Māori and the English translations of the second article of the treaty?",
        value: "What is the key difference between the Māori and the English translations of the second article of the treaty?"
    },
    { text: "What are the key principals when engaging with Māori?", value: "What are the key principals when engaging with Māori?" },
    { text: "What is the role of the Waitangi Tribunal?", value: "What is the role of the Waitangi Tribunal?" }
];

interface Props {
    onExampleClicked: (value: string) => void;
}

export const ExampleList = ({ onExampleClicked }: Props) => {
    return (
        <ul className={styles.examplesNavList}>
            {EXAMPLES.map((x, i) => (
                <li key={i}>
                    <Example text={x.text} value={x.value} onClick={onExampleClicked} />
                </li>
            ))}
        </ul>
    );
};
